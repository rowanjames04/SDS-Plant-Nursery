import sys
import time
import unittest


SPRINT_TEST_MODULES = [
    ("Sprint 0 - setup and configuration", "tests.test_sprint0_setup"),
    ("Sprint 1 - catalog, users, carts, and wishlist", "tests.test_sprint1_catalog_users"),
    ("Sprint 2 - inventory, images, order snapshots, and delivery scope", "tests.test_sprint2_inventory_scope"),
    ("Sprint 3 - admin management", "tests.test_sprint3_admin"),
    ("Sprint 4 - checkout and fulfilment", "tests.test_sprint4_checkout_fulfillment"),
]


class SimpleTestResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.elapsed = 0.0
        self._test_started_at = None

    def getDescription(self, test):
        return test._testMethodName

    def _duration(self):
        if self._test_started_at is None:
            return 0.0
        return time.perf_counter() - self._test_started_at

    def _write_status(self, status):
        duration = self._duration()
        self.elapsed += duration
        self.stream.writeln(f"{status} ({duration:.3f}s)")
        self._test_started_at = None

    def startTest(self, test):
        unittest.TestResult.startTest(self, test)
        self._test_started_at = time.perf_counter()
        self.stream.write(f"{self.getDescription(test)} ... ")
        self.stream.flush()

    def addSuccess(self, test):
        unittest.TestResult.addSuccess(self, test)
        self._write_status("OK")

    def addFailure(self, test, err):
        unittest.TestResult.addFailure(self, test, err)
        self._write_status("FAIL")

    def addError(self, test, err):
        unittest.TestResult.addError(self, test, err)
        self._write_status("ERROR")

    def addSkip(self, test, reason):
        unittest.TestResult.addSkip(self, test, reason)
        self._write_status(f"SKIP: {reason}")


class SimpleTestRunner(unittest.TextTestRunner):
    resultclass = SimpleTestResult

    def run(self, test):
        result = self._makeResult()
        test(result)
        return result


def main():
    loader = unittest.TestLoader()
    runner = SimpleTestRunner(stream=sys.stdout)
    overall_result = unittest.TestResult()
    overall_elapsed = 0.0

    for label, module_name in SPRINT_TEST_MODULES:
        print(f"\n=== {label} ===", flush=True)
        suite = loader.loadTestsFromName(module_name)
        result = runner.run(suite)
        overall_elapsed += result.elapsed
        print(f"Ran {result.testsRun} tests in {result.elapsed:.3f}s")
        overall_result.testsRun += result.testsRun
        overall_result.failures.extend(result.failures)
        overall_result.errors.extend(result.errors)
        overall_result.skipped.extend(result.skipped)
        overall_result.expectedFailures.extend(result.expectedFailures)
        overall_result.unexpectedSuccesses.extend(result.unexpectedSuccesses)

    print("\n=== Overall summary ===")
    print(f"Tests run: {overall_result.testsRun}")
    print(f"Time: {overall_elapsed:.3f}s")
    print(f"Failures: {len(overall_result.failures)}")
    print(f"Errors: {len(overall_result.errors)}")
    print(f"Skipped: {len(overall_result.skipped)}")

    if overall_result.failures or overall_result.errors or overall_result.unexpectedSuccesses:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
