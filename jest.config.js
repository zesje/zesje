module.exports = {
  'moduleNameMapper': {
    '\\.(css|md)$': 'identity-obj-proxy'
  },
  'testPathIgnorePatterns': ['/node_modules/', '/.yarn-cache/'],
  'setupTestFrameworkScriptFile': '<rootDir>testSetup.js'
}
