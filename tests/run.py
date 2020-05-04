import unittest
import units
import scenarios

runner = unittest.TextTestRunner(verbosity=2)
print("Processing unit tests...")
runner.run(units.getUnitTestSuit())
print("Processing scenario tests...")
runner.run(scenarios.getScenarioTestSuit())
