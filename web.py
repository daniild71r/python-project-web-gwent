from abc import abstractmethod
import flask
import mechanics
import os


class Texts:
    def __init__(self):
        textSource = open("static/texts.txt", "r")
        lines = textSource.read().splitlines()
        iterator = iter(lines)
        self.playerNames = list()
        for i in range(2):
            self.playerNames.append(next(iterator))

        self.difficultyOptions = list()
        for i in range(4):
            self.difficultyOptions.append(next(iterator))
        self.fractionOptions = list()
        for i in range(2):
            self.fractionOptions.append(next(iterator))

        self.playerLabel = list()
        for i in range(3):
            self.playerLabel.append(next(iterator))

        self.rowTypes = list()
        for i in range(3):
            self.rowTypes.append(next(iterator))

        self.roundEnded = next(iterator)
        self.gameEnded = next(iterator)

        self.endingMessage = list()
        for i in range(4):
            self.endingMessage.append(next(iterator))
        self.endingActions = list()
        for i in range(3):
            self.endingActions.append(next(iterator))
        textSource.close()


class Labeler:
    def __init__(self):
        pass

    def getUnitLabel(self, unit):
        return str(unit.strength)

    def getCommanderLabel(self, commander):
        return "(" + str(commander.strength) + ")"

    def getSpyLabel(self, spy):
        return "[" + str(spy.strength) + "]"

    def getRowLabel(self, row):
        if len(row.units) > 0:
            return " ".join(unit.acceptLabeler(self) for unit in row.units)
        else:
            return "-"

    def getPlayerLabel(self, player):
        count = player.countUnits()
        label = "<br>".join(texts.playerLabel[0:2])
        return label.format(
            player.name, texts.fractionOptions[player.fraction],
            player.roundsWon, count[0], count[1]
        )

    def getAILabel(self, playerAI):
        count = playerAI.countUnits()
        label = "<br>".join(texts.playerLabel)
        return label.format(
            playerAI.name, texts.fractionOptions[playerAI.fraction],
            playerAI.roundsWon, count[0], count[1],
            texts.difficultyOptions[playerAI.difficulty]
        )


class ButtonLabeler(Labeler):
    def getUnitLabel(self, unit):
        return texts.rowTypes[unit.rowType] + " " + str(unit.strength)

    def getCommanderLabel(self, commander):
        return ("commander " + texts.rowTypes[commander.rowType] + " " +
                str(commander.strength))

    def getSpyLabel(self, spy):
        return "spy " + texts.rowTypes[spy.rowType] + " " + str(spy.strength)


class InterfaceElement:
    @abstractmethod
    def update(self):
        pass


class PlayerElement(InterfaceElement):
    def __init__(self, manager, opponent=False):
        if not opponent:
            self.player = manager.game.player1
        else:
            self.player = manager.game.player2
        labeler = Labeler()
        self.state = self.player.acceptLabeler(labeler)

    def update(self):
        labeler = Labeler()
        self.state = self.player.acceptLabeler(labeler)


class RowsElement(InterfaceElement):
    def __init__(self, manager, opponent=False):
        self.manager = manager
        if not opponent:
            self.player = manager.game.player1
        else:
            self.player = manager.game.player2
        self.rows = list("-" for i in range(mechanics.rows))
        self.rowSums = list(0 for i in range(mechanics.rows))
        self.sum = 0

    def update(self, rowType):
        row = self.player.rows[rowType]
        labeler = Labeler()
        self.rows[rowType] = row.acceptLabeler(labeler)
        self.sum -= self.rowSums[rowType]
        self.rowSums[rowType] = row.sum
        self.sum += self.rowSums[rowType]


class UnitsElement(InterfaceElement):
    def __init__(self, manager):
        self.manager = manager
        self.player = manager.game.player1
        self.buttonLabels = list()
        self.update()

    def update(self):
        unitCounter = 0
        for unit in self.manager.game.player1.deck:
            if unit.condition == mechanics.ConditionType.inHand and \
                    unitCounter >= len(self.buttonLabels):
                self.addUnit(unitCounter)
            unitCounter += 1

    def addUnit(self, i):
        unit = self.player.deck[i]
        buttonLabeler = ButtonLabeler()
        self.buttonLabels.append(unit.acceptLabeler(buttonLabeler))


class InterfaceManager:
    def __init__(self, game):
        self.game = game
        self.playerInterface1 = PlayerElement(self)
        self.playerInterface2 = PlayerElement(self, True)
        self.rowsInterface1 = RowsElement(self)
        self.rowsInterface2 = RowsElement(self, True)
        self.unitsInterface = UnitsElement(self)

    def processUnit(self, index):
        self.unitsInterface.buttonLabels[index] = None
        self.playerInterface1.update()
        rowType = self.game.player1.deck[index].rowType
        self.rowsInterface1.update(rowType)
        self.unitsInterface.update()

    def processOppUnit(self, rowType):
        self.playerInterface2.update()
        self.rowsInterface2.update(rowType)

    def updateAll(self):
        self.playerInterface1.update()
        self.playerInterface2.update()
        for i in range(mechanics.rows):
            self.rowsInterface1.update(i)
            self.rowsInterface2.update(i)
        self.unitsInterface.update()


class GameState:
    configuringDifficulty = 0
    configuringFraction = 1
    playing = 2
    notifyingPass = 3
    displayingRules = 4
    notifyingEndRound = 5
    notifyingEndGame = 6


class Game:
    def __init__(self):
        self.state = GameState.configuringDifficulty
        self.manager = None
        self.difficulty = 0
        self.fraction = 0
        self.player1 = None
        self.player2 = None
        self.opponentPassed = False
        self.message = "OK, boomer"

    def processDifficulty(self, choice):
        self.difficulty = choice
        self.state = GameState.configuringFraction

    def processFraction(self, choice):
        self.fraction = choice
        self.state = GameState.playing
        self.startGame()

    def processUnit(self, index):
        self.player1.deck[index].play()
        self.manager.processUnit(index)
        self.switchTurns()

    def processPass(self):
        if not self.opponentPassed:
            self.opponentTurn(lastTurn=True)
        self.endRound()

    def startGame(self):
        self.state = GameState.playing
        self.player1 = mechanics.Player(texts.playerNames[0], self.fraction)
        self.player2 = mechanics.AI(texts.playerNames[1], self.difficulty)
        if difficulty == 3:
            self.player2 = mechanics.getCheatingAI(self.player2)
        self.player1.generateDeck(deckGenerator)
        self.player2.generateDeck(deckGenerator)
        self.manager = InterfaceManager(self)

    def switchTurns(self):
        if self.opponentPassed:
            self.endRound()
        else:
            self.opponentTurn()

    def opponentTurn(self, lastTurn=False):
        unit = self.player2.makeTurn(self.player1, lastTurn)
        if unit != 0:
            unit.play()
            self.manager.processOppUnit(unit.rowType)
        elif not lastTurn:
            self.opponentPassed = True
            self.state = GameState.notifyingPass

    def endRound(self):
        sum1 = self.player1.getSum()
        sum2 = self.player2.getSum()
        lines = [line + "<br>" for line in texts.endingMessage]

        if self.opponentPassed:
            lines[0] = lines[0].format(self.player2.name, self.player1.name)
        else:
            lines[0] = lines[0].format(self.player1.name, self.player2.name)
        self.opponentPassed = False

        gameEnded = False
        if sum1 > sum2:
            action = texts.endingActions[0]
            roundsWon1 = self.player1.winRound()
            if roundsWon1 == mechanics.roundWinCondition:
                gameEnded = True
        elif sum1 == sum2:
            action = texts.endingActions[1]
        else:
            action = texts.endingActions[2]
            roundsWon2 = self.player2.winRound()
            if roundsWon2 == mechanics.roundWinCondition:
                gameEnded = True
        lines[1] = lines[1].format(sum1, sum2, action)

        if gameEnded:
            lines[2] = lines[2].format(action)
            self.message = lines[0] + lines[1] + lines[2] + lines[3]
            self.state = GameState.notifyingEndGame
        else:
            self.message = lines[0] + lines[1] + lines[3]
            self.state = GameState.notifyingEndRound

    def processContinue(self):
        if self.state == GameState.notifyingEndRound:
            self.state = GameState.playing
            self.newRound()
        else:
            self.startGame()

    def clearBoard(self):
        self.player1.clearRows()
        self.player2.clearRows()
        self.manager.updateAll()

    def newRound(self):
        self.player1.drawCard()
        self.player2.drawCard()
        self.clearBoard()


texts = Texts()
gwentWeb = flask.Flask(__name__)
deckGenerator = mechanics.DeckGenerator()
gwentGame = Game()
if __name__ == '__main__':
    gwentWeb.run()


@gwentWeb.route("/favicon.ico")
def favicon():
    return flask.send_from_directory(
        os.path.join(gwentWeb.root_path, "static"),
        "icon.ico"
    )


@gwentWeb.route("/", methods=["GET"])
def get():
    labels = list()
    if gwentGame.state == GameState.playing:
        labels = gwentGame.manager.unitsInterface.buttonLabels
    return flask.render_template(
        "index.html",
        game=gwentGame,
        manager=gwentGame.manager,
        buttons=zip(range(len(labels)), labels)
    )


@gwentWeb.route("/difficulty", methods=["POST"])
def difficulty():
    choice = 0
    if "medium" in flask.request.form:
        choice = 1
    elif "hard" in flask.request.form:
        choice = 2
    elif "cheater" in flask.request.form:
        choice = 3
    gwentGame.processDifficulty(choice)
    return flask.redirect("/")


@gwentWeb.route("/fraction", methods=["POST"])
def fraction():
    choice = 0
    if "nilfgaard" in flask.request.form:
        choice = 1
    gwentGame.processFraction(choice)
    return flask.redirect("/")


@gwentWeb.route("/play", methods=["POST"])
def play():
    index = int(flask.request.form["unit"])
    gwentGame.processUnit(index)
    return flask.redirect("/")


@gwentWeb.route("/restart", methods=["POST"])
def restart():
    gwentGame.state = GameState.configuringDifficulty
    return flask.redirect("/")


@gwentWeb.route("/rules", methods=["POST"])
def rules():
    gwentGame.state = GameState.displayingRules
    return flask.redirect("/")


@gwentWeb.route("/dismissRules", methods=["POST"])
def dismissRules():
    gwentGame.state = GameState.playing
    return flask.redirect("/")


@gwentWeb.route("/pass", methods=["POST"])
def passRound():
    gwentGame.processPass()
    return flask.redirect("/")


@gwentWeb.route("/dismissPass", methods=["POST"])
def dismissPass():
    gwentGame.state = GameState.playing
    return flask.redirect("/")


@gwentWeb.route("/continue", methods=["POST"])
def continuePlaying():
    gwentGame.processContinue()
    return flask.redirect("/")
