const webpack = require('webpack')
const merge = require('webpack-merge')
const common = require('./webpack.common.js')

const commitHash = require('child_process')
  .execSync('git rev-parse --short HEAD')
  .toString()
  .trim()

module.exports = merge(common, {
  mode: 'development',
  module: {
    rules: [
      { test: /\.css$/, use: [ 'style-loader', 'css-loader' ] }
    ]
  },
  devServer: {
    hot: true,
    inline: true,
    proxy: {
      '/api': {
        target: 'http://localhost:5000'
      }
    },
    historyApiFallback: true,
    port: 8881,
    publicPath: '/',
    host: 'localhost',
    overlay: {
      warnings: true,
      errors: true
    }
  },
  plugins: [
    new webpack.EvalSourceMapDevToolPlugin({
      sourceURLTemplate: module => `/${module.identifier}`
    }),
    new webpack.DefinePlugin({
      __COMMIT_HASH__: JSON.stringify(commitHash + '-dev')
    })
  ]
})
