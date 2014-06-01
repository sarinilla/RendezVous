import os
import unittest

def runtests(path, separate=False):

    """Run all test cases in all modules located at path.

    Note that modules containing test cases must begin with 'test',
    and test case classes must begin with 'Test'.

    The optional separate argument, if set to True, forces each TestCase
    to be executed separately.  By default, all tests are aggregated to a
    single TestSuite and run together, so that the latest console output
    shows the total number of tests run.

    """

    full_suite = unittest.TestSuite()
    for (directory, subdirs, files) in os.walk(path):

        # We only care about packages
        if '__init__.py' not in files:
            continue

        # Get the correct dot-separated package name
        package_name = directory[len(path):]
        package_name = package_name.replace(os.sep, '.')
        package_name = package_name.strip('.')

        # Browse package
        for filename in files:

            # We only care about Python modules
            if not filename.endswith('.py'):
                continue

            # We only care about test modules
            if not filename.startswith('test'):
                continue

            # Import * from module
            module_name = "%s.%s" % (package_name, filename[:-3])
            module = __import__(module_name, globals(), locals(), ['*'])

            # Browse module
            for class_name in dir(module):

                # We only care about test classes
                if not class_name.startswith('Test'):
                    continue

                # Load tests from class
                test_case = module.__dict__[class_name]
                suite = unittest.TestLoader().loadTestsFromTestCase(test_case)
                if separate:
                    # Run tests for this class only
                    unittest.TextTestRunner().run(suite)
                else:
                    full_suite.addTests(suite)

    # Run collected tests from all modules
    if not separate:
        unittest.TextTestRunner().run(full_suite)


if __name__ == '__main__':
    runtests('.')
