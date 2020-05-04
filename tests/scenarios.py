import unittest
from web import Labeler
import mechanics


class TestBoardInteraction(unittest.TestCase):
    def setUp(self):
        self.player = mechanics.Player("Test Player", 0)
        self.deckGenerator = mechanics.DeckGenerator()
        self.player.generateDeck(self.deckGenerator)
        for i in range(mechanics.Player.deckSize):
            self.player.drawCard()

    def testBasicUnitPlay(self):
        rowSums = list(0 for i in range(mechanics.rows))
        for unit in self.player.deck:
            if (not isinstance(unit, mechanics.Commander) and
                    not isinstance(unit, mechanics.Spy)):
                unit.play()
                rowSums[unit.rowType] += unit.strength
                self.assertEqual(rowSums[unit.rowType],
                                 self.player.rows[unit.rowType].sum)

    def testCommanderPlay(self):
        for unit in self.player.deck:
            if isinstance(unit, mechanics.Spy):
                pass
            elif isinstance(unit, mechanics.Commander):
                row = self.player.rows[unit.rowType]
                expectedSum = (row.sum + len(row.units) + unit.strength +
                               row.activeCommanders)
                unit.play()
                self.assertEqual(row.sum, expectedSum)
            else:
                unit.play()

    def testSpyPlay(self):
        for i in range(mechanics.Player.handSize, mechanics.Player.deckSize):
            self.player.deck[i].conditionType = mechanics.ConditionType.inDeck
        for unit in self.player.deck:
            if isinstance(unit, mechanics.Spy):
                inHand, inDeck = self.player.countUnits()
                unit.play()
                if inDeck >= 2:
                    self.assertEqual(inHand + 1, self.player.countUnits()[0])
                elif inDeck == 1:
                    self.assertEqual(inHand, self.player.countUnits()[0])
                else:
                    self.assertEqual(inHand - 1, self.player.countUnits()[0])

    def testBoardClear(self):
        for unit in self.player.deck:
            unit.play()
            self.player.clearRows()
            self.assertEqual(sum(self.player.rows[i].sum for i in range(3)), 0)
        self.player.refresh(self.deckGenerator)
        for unit in self.player.deck:
            unit.play()
        self.assertGreater(sum(self.player.rows[i].sum for i in range(3)), 0)


class TestAI(unittest.TestCase):
    def setUp(self):
        self.playerAI = mechanics.AI("Test Player", 2)
        self.deckGenerator = mechanics.DeckGenerator()
        self.playerAI.generateDeck(self.deckGenerator)

    def testUnitOptions(self):
        originalOptions = self.playerAI.getUnitOptions()
        options = list()
        for unit in self.playerAI.deck:
            if unit.condition == mechanics.ConditionType.inHand:
                options.append(unit)
        self.assertEqual(len(originalOptions), len(options))
        counter = 0
        for unit in options:
            if not isinstance(unit, mechanics.Spy):
                counter += 1
                unit.play()
        expected = len(originalOptions) - counter
        self.assertEqual(expected, len(self.playerAI.getUnitOptions()))

    def testMakeTurn(self):
        opponent = mechanics.Player("Test Player", 0)
        opponent.generateDeck(self.deckGenerator)
        for i in range(mechanics.Player.deckSize):
            self.playerAI.drawCard()
            choice = self.playerAI.makeTurn(opponent)
            if choice != 0:
                self.assertTrue(choice in self.playerAI.deck and
                                choice.condition ==
                                mechanics.ConditionType.inHand)
                choice.play()


class TestCheats(unittest.TestCase):
    def setUp(self):
        deckGenerator = mechanics.DeckGenerator()
        self.player1 = mechanics.HandBuffingAI(mechanics.AI("Test Player", 3))
        self.player2 = mechanics.CardDrawingAI(mechanics.AI("Test Player", 3))
        self.player1.generateDeck(deckGenerator)
        self.player2.generateDeck(deckGenerator)

    def testCheats(self):
        initialSum = sum(unit.strength for unit in self.player1.deck)
        counter = 0
        for i in range(mechanics.Player.deckSize):
            if len(self.player1.getUnitOptions()) > 0:
                counter += 1
            choice1 = self.player1.makeTurn(self.player2)
            if choice1 != 0:
                choice1.play()
            choice2 = self.player2.makeTurn(self.player1)
            if choice2 != 0:
                choice2.play()
        self.assertGreaterEqual(
            sum(unit.strength for unit in self.player1.deck),
            initialSum + 2 * counter
        )


class TestLabelers(unittest.TestCase):
    def setUp(self):
        self.labeler = Labeler()
        self.player = mechanics.Player("Test Player", 0)
        self.deckGenerator = mechanics.DeckGenerator()
        self.player.generateDeck(self.deckGenerator)

    def testUnitLabeling(self):
        for i in range(mechanics.Player.handSize):
            unit = self.player.deck[i]
            label = unit.acceptLabeler(self.labeler)
            if isinstance(unit, mechanics.Commander):
                self.assertEqual(label, "(" + str(unit.strength) + ")")
            elif isinstance(unit, mechanics.Spy):
                self.assertEqual(label, "[" + str(unit.strength) + "]")
            else:
                self.assertEqual(label, str(unit.strength))

    def rowLabeling(self):
        count = list(0 for i in range(mechanics.rows))
        for i in range(mechanics.Player.handSize):
            unit = self.player.deck[i]
            unit.play()
            count[unit.rowType] += 1
        labels = [self.player.rows[i].acceptLabeler(self.labeler) for i in
                  range(mechanics.rows)]
        for i in range(mechanics.rows):
            self.assertEqual(len(labels[i].split(" ")), count[i])


def getScenarioTestSuit():
    suit = unittest.TestSuite()
    suit.addTest(TestBoardInteraction("testBasicUnitPlay"))
    suit.addTest(TestBoardInteraction("testCommanderPlay"))
    suit.addTest(TestBoardInteraction("testSpyPlay"))
    suit.addTest(TestBoardInteraction("testBoardClear"))
    suit.addTest(TestAI("testUnitOptions"))
    suit.addTest(TestAI("testMakeTurn"))
    suit.addTest(TestCheats("testCheats"))
    suit.addTest(TestLabelers("testUnitLabeling"))
    suit.addTest(TestLabelers("rowLabeling"))
    return suit
