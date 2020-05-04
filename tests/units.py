import unittest
import mechanics


class TestCreators(unittest.TestCase):
    def testCreators(self):
        unitCreator = mechanics.UnitCreator()
        for i in range(100):
            unit = unitCreator.create()
            within = 1 <= unit.strength <= 10 and 0 <= unit.rowType <= 2
            self.assertTrue(within)

        commanderCreator = mechanics.CommanderCreator()
        for i in range(100):
            unit = commanderCreator.create()
            within = 1 <= unit.strength <= 8 and 0 <= unit.rowType <= 2
            self.assertTrue(within)

        spyCreator = mechanics.SpyCreator()
        for i in range(100):
            unit = spyCreator.create()
            within = 1 <= unit.strength <= 6 and 0 <= unit.rowType <= 2
            self.assertTrue(within)


class TestDeckGeneration(unittest.TestCase):
    def setUp(self):
        self.player = mechanics.Player("Test Player", 0)
        self.deckGenerator = mechanics.DeckGenerator()
        self.player.generateDeck(self.deckGenerator)

    def testCopyCorrectness(self):
        used = list(False for i in range(len(self.player.deck)))
        success = True
        for unit in self.deckGenerator.deckPreset:
            unitSuccess = False
            for i in range(len(self.player.deck)):
                unit2 = self.player.deck[i]
                if (unit.strength == unit2.strength and
                        unit.rowType == unit2.rowType and not used[i]):
                    unitSuccess = True
                    used[i] = True
                    break
            success = success and unitSuccess
        self.assertTrue(success, "not all units copied")

    def testUnitNumbers(self):
        commanders = 0
        spies = 0
        inHand = 0
        for unit in self.player.deck:
            if unit.condition == mechanics.ConditionType.inHand:
                inHand += 1
            if isinstance(unit, mechanics.Commander):
                commanders += 1
            elif isinstance(unit, mechanics.Spy):
                spies += 1
        self.assertEqual(len(self.player.deck), mechanics.Player.deckSize)
        self.assertEqual(inHand, mechanics.Player.handSize,
                         "incorrect hand size")
        self.assertEqual(commanders, mechanics.DeckGenerator.firstUnique,
                         "incorrect number of commanders")
        self.assertEqual(spies, mechanics.DeckGenerator.secondUnique,
                         "incorrect number of spies")


class TestPlayerBasicMethods(unittest.TestCase):
    def setUp(self):
        self.player = mechanics.Player("Test Player", 0)
        self.deckGenerator = mechanics.DeckGenerator()
        self.player.generateDeck(self.deckGenerator)

    def testUnitCount(self):
        inHand0, inDeck0 = self.player.countUnits()
        inHand = 0
        inDeck = 0
        for unit in self.player.deck:
            if unit.condition == mechanics.ConditionType.inHand:
                inHand += 1
                unit.condition = mechanics.ConditionType.dead
            elif unit.condition == mechanics.ConditionType.inDeck:
                inDeck += 1
                unit.condition = mechanics.ConditionType.dead
        self.assertEqual(inHand0, inHand)
        self.assertEqual(inDeck0, inDeck)
        inHand0, inDeck0 = self.player.countUnits()
        self.assertEqual(inHand0, 0)
        self.assertEqual(inDeck0, 0)

    def testDrawCard(self):
        inHand = self.player.countUnits()[0]
        for i in range(100):
            self.player.drawCard()
            inHand0 = self.player.countUnits()[0]
            if inHand < mechanics.Player.deckSize:
                self.assertEqual(inHand0, inHand + 1)
            else:
                self.assertEqual(inHand0, inHand)
            inHand = inHand0

    def testWinRound(self):
        roundsWon = self.player.winRound()
        for i in range(100):
            roundsWon0 = self.player.winRound()
            self.assertEqual(roundsWon + 1, roundsWon0)
            roundsWon = roundsWon0


def getUnitTestSuit():
    suit = unittest.TestSuite()
    suit.addTest(TestCreators("testCreators"))
    suit.addTest(TestDeckGeneration("testCopyCorrectness"))
    suit.addTest(TestDeckGeneration("testUnitNumbers"))
    suit.addTest(TestPlayerBasicMethods("testUnitCount"))
    suit.addTest(TestPlayerBasicMethods("testDrawCard"))
    suit.addTest(TestPlayerBasicMethods("testWinRound"))
    return suit
