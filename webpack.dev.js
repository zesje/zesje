const webpack = require('webpack')
const { merge } = require('webpack-merge')
const common = require('./webpack.common.js')

module.exports = merge(common, {
  mode: 'development',
  module: {
    rules: [
      { test: /\.css$/, use: ['style-loader', 'css-loader'] },
      { test: /\.s(c|a)ss$/, use: ['style-loader', 'css-loader', 'sass-loader'] }
    ]
  },
  devServer: {
    hot: true,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000'
      }
    },
    historyApiFallback: true,
    port: 8881,
    static: {
      publicPath: '/'
    },
    host: 'localhost',
    client: {
      overlay: {
        warnings: true,
        errors: true
      }
    }
  },
  watchOptions: {
    ignored: '**/node_modules/'
  },
  plugins: [
    new webpack.EvalSourceMapDevToolPlugin({
      sourceURLTemplate: module => `/${module.identifier}`
    })
  ],
  resolve: { alias: { 'react-dom': '@hot-loader/react-dom' } }
})
