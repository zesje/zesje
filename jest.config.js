module.exports = {
  moduleNameMapper: {
    '\\.(css|md)$': 'identity-obj-proxy'
  },
  testPathIgnorePatterns: ['/node_modules/', '/.yarn-cache/'],
  modulePathIgnorePatterns: ['.yarn-cache'],
  setupTestFrameworkScriptFile: '<rootDir>testSetup.js',
  reporters: ['default', 'jest-junit']
}
