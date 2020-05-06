from abc import abstractmethod
from copy import copy
from random import randint, choice, shuffle

rows = 3
roundWinCondition = 2


class RowType:
    melee = 0
    ranged = 1
    siege = 2


class ConditionType:
    inDeck = 0
    inHand = 1
    inGame = 2
    dead = 3


class Fraction:
    north = 0
    nilfgaard = 1


class Unit:
    def __init__(self, rowType, strength):
        self.player = None
        self.rowType = rowType
        self.strength = strength
        self.condition = ConditionType.inDeck

    def setPlayer(self, player):
        self.player = player

    def play(self):
        row = self.player.rows[self.rowType]
        self.condition = ConditionType.inGame
        self.strength += row.activeCommanders
        row.units.append(self)
        row.updateSum()

    def acceptLabeler(self, labeler):
        return labeler.getUnitLabel(self)

    unitRate = 5


class Commander(Unit):
    def __init__(self, rowType, strength):
        super().__init__(rowType, strength)

    def play(self):
        row = self.player.rows[self.rowType]
        self.condition = ConditionType.inGame
        self.strength += row.activeCommanders
        for unit in row.units:
            unit.strength += 1
        row.units.append(self)
        row.activeCommanders += 1
        row.updateSum()

    def acceptLabeler(self, labeler):
        return labeler.getCommanderLabel(self)


class Spy(Unit):
    def __init__(self, rowType, strength):
        super().__init__(rowType, strength)

    def play(self):
        row = self.player.rows[self.rowType]
        self.condition = ConditionType.inGame
        self.strength += row.activeCommanders
        row.units.append(self)
        for i in range(2):
            self.player.drawCard()
        row.updateSum()

    def acceptLabeler(self, labeler):
        return labeler.getSpyLabel(self)


class Creator:
    @abstractmethod
    def create(self):
        pass

    @staticmethod
    @abstractmethod
    def generateStrength():
        pass

    @staticmethod
    def generateRowType():
        return randint(0, rows - 1)


class UnitCreator(Creator):
    def __init__(self):
        pass

    def create(self):
        rowType = UnitCreator.generateRowType()
        strength = UnitCreator.generateStrength()
        return Unit(rowType, strength)

    @staticmethod
    @abstractmethod
    def generateStrength():
        strength = randint(1, 2) * randint(1, 3) + randint(1, 4)
        return strength


class CommanderCreator(Creator):
    def __init__(self):
        pass

    def create(self):
        rowType = CommanderCreator.generateRowType()
        strength = CommanderCreator.generateStrength()
        return Commander(rowType, strength)

    @staticmethod
    @abstractmethod
    def generateStrength():
        strength = randint(1, 2) * randint(1, 2) + randint(1, 4)
        return strength


class SpyCreator(Creator):
    def __init__(self):
        pass

    def create(self):
        rowType = SpyCreator.generateRowType()
        strength = SpyCreator.generateStrength()
        return Spy(rowType, strength)

    @staticmethod
    @abstractmethod
    def generateStrength():
        strength = randint(1, 2) * randint(1, 3)
        return strength


class Row:
    def __init__(self, rowType):
        self.rowType = rowType
        self.units = list()
        self.sum = 0
        self.activeCommanders = 0

    def updateSum(self):
        self.sum = 0
        for unit in self.units:
            self.sum += unit.strength

    def acceptLabeler(self, labeler):
        return labeler.getRowLabel(self)


class Deck(list):
    def __init__(self, *args):
        super().__init__(*args)

    def getCopy(self):
        newDeck = Deck()
        for unit in self:
            newDeck.append(copy(unit))
        return newDeck


class DeckGenerator:
    def __init__(self):
        self.deckPreset = Deck()
        for i in range(DeckGenerator.basicUnits):
            unitCreator = UnitCreator()
            self.deckPreset.append(unitCreator.create())

    def generateDeck(self, player):
        newDeck = self.deckPreset.getCopy()
        commanderCreator = CommanderCreator()
        spyCreator = SpyCreator()

        if player.fraction == Fraction.north:
            for i in range(DeckGenerator.firstUnique):
                newDeck.append(commanderCreator.create())
                newDeck[-1].strength += 2
            for i in range(DeckGenerator.secondUnique):
                newDeck.append(spyCreator.create())
        elif player.fraction == Fraction.nilfgaard:
            for i in range(DeckGenerator.firstUnique):
                newDeck.append(spyCreator.create())
                newDeck[-1].strength += 2
            for i in range(DeckGenerator.secondUnique):
                newDeck.append(commanderCreator.create())

        for i in range(Player.deckSize):
            newDeck[i].setPlayer(player)
        shuffle(newDeck)
        for i in range(Player.handSize):
            newDeck[i].condition = ConditionType.inHand
        return newDeck

    basicUnits = 16
    firstUnique = 6
    secondUnique = 3


class Player:
    def __init__(self, name, fraction=Fraction.north):
        self.name = name
        self.fraction = fraction
        self.roundsWon = 0
        self.deck = list()
        self.deckTop = 0
        self.rows = [Row(i) for i in range(rows)]

    def generateDeck(self, deckGenerator):
        self.innerGenerateDeck(deckGenerator)

    def innerGenerateDeck(self, deckGenerator):
        self.deck = deckGenerator.generateDeck(self)
        self.deckTop = Player.handSize

    def countUnits(self):
        inHand = 0
        inDeck = 0
        for unit in self.deck:
            if unit.condition == ConditionType.inHand:
                inHand += 1
            elif unit.condition == ConditionType.inDeck:
                inDeck += 1
        return inHand, inDeck

    def getSum(self):
        result = 0
        for i in range(rows):
            result += self.rows[i].sum
        return result

    def drawCard(self):
        if self.deckTop < Player.deckSize:
            self.deck[self.deckTop].condition = ConditionType.inHand
            self.deckTop += 1

    def winRound(self):
        self.roundsWon += 1
        return self.roundsWon

    def clearRows(self):
        for i in range(rows):
            for unit in self.rows[i].units:
                if unit.condition == ConditionType.inGame:
                    unit.condition = ConditionType.dead
            self.rows[i] = Row(i)

    def refresh(self, deckGenerator):
        self.clearRows()
        self.deck = list()
        self.generateDeck(deckGenerator)
        self.roundsWon = 0

    def acceptLabeler(self, labeler):
        return labeler.getPlayerLabel(self)

    deckSize = 25
    handSize = 10


class AI(Player):
    def __init__(self, name, difficulty=0):
        super().__init__(name)
        self.difficulty = difficulty

    def generateDeck(self, deckGenerator):
        self.innerGenerateDeck(deckGenerator)
        for unit in self.deck:
            unit.strength += randint(0, self.difficulty + 1)

    def getUnitOptions(self):
        options = list()
        for unit in self.deck:
            if unit.condition == ConditionType.inHand:
                options.append(unit)
        return options

    def makeTurn(self, opponent, opponentPassed=False):
        mySum = self.getSum()
        opponentSum = opponent.getSum()

        # if opponent passed, then try to finish him
        if opponentPassed:
            if mySum > opponentSum:
                return 0
            options = self.getUnitOptions()
            for unit in options:
                add = unit.strength + self.rows[unit.rowType].activeCommanders
                if mySum + add > opponentSum:
                    return unit
            return 0

        # if the situation is not critical, then possibly pass
        if mySum > opponentSum + AI.strengthThreshold:
            return 0
        if max(self.roundsWon, opponent.roundsWon) < roundWinCondition - 1:
            passTry = randint(0, AI.passRate)
            if passTry == AI.passRate:
                return 0

        # case is not that simple, so make a random turn :)
        options = self.getUnitOptions()
        return choice(options) if len(options) > 0 else 0

    def acceptLabeler(self, labeler):
        return labeler.getAILabel(self)

    strengthThreshold = 15
    passRate = 5


class CheatingAI:
    @abstractmethod
    def makeTurn(self, opponent, opponentPassed=False):
        pass

    @abstractmethod
    def generateDeck(self, deckGenerator):
        pass

    methodsReplaced = ["makeTurn", "generateDeck"]


class CardDrawingAI(CheatingAI):
    def __init__(self, playerAI):
        self.playerAI = playerAI

    def makeTurn(self, opponent, opponentPassed=False):
        drawAmount = randint(0, 1)
        for i in range(drawAmount):
            self.playerAI.drawCard()
        return self.playerAI.makeTurn(opponent, opponentPassed)

    def generateDeck(self, deckGenerator):
        self.playerAI.innerGenerateDeck(deckGenerator)

    def __getattr__(self, key):
        return self.playerAI.__getattribute__(key)


class HandBuffingAI(CheatingAI):
    def __init__(self, playerAI):
        self.playerAI = playerAI

    def makeTurn(self, opponent, opponentPassed=False):
        options = self.playerAI.getUnitOptions()
        if len(options) > 0:
            choice(options).strength += randint(2, 3)
        return self.playerAI.makeTurn(opponent, opponentPassed)

    def generateDeck(self, deckGenerator):
        self.playerAI.innerGenerateDeck(deckGenerator)

    def __getattr__(self, key):
        return self.playerAI.__getattribute__(key)


def getCheatingAI(playerAI):
    cheatType = randint(0, 1)
    if cheatType == 0:
        return CardDrawingAI(playerAI)
    elif cheatType == 1:
        return HandBuffingAI(playerAI)
