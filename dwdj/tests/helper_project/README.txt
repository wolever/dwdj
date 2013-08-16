NOTE: because of path munging that Django does, it's important that the helper
project be a Python package, but it must *not* be inside another package. Hence
this non-package directory between the test package and the 'helper_project'
package.
