/*
    ./webpack.config.js
*/
const path = require('path')
const webpack = require('webpack')

const HtmlWebpackPlugin = require('html-webpack-plugin')
const HtmlWebpackPluginConfig = new HtmlWebpackPlugin({
  template: './client/index.html',
  favicon: './client/favicon.ico',
  filename: 'index.html',
  inject: 'body'
})

const zesjeVersion = require('child_process')
  .execSync('python3 zesje/_version.py')
  .toString()
  .trim()

module.exports = {
  entry: './client/index.jsx',
  output: {
    path: path.resolve('zesje/static'),
    filename: 'index_bundle.js',
    publicPath: '/',
    globalObject: 'this'
  },
  module: {
    rules: [
      { test: /\.(jsx|js)$/, loader: 'babel-loader', options: { cacheDirectory: true }, exclude: /node_modules/ },
      { test: /\.(woff(2)?|ttf|eot|svg|otf)(\?v=\d+\.\d+\.\d+)?$/, type: 'asset/resource' },
      { test: /\.md$/, use: [{ loader: 'html-loader' }, { loader: 'markdown-loader' }] },
      { test: /\.(gif|jpeg|jpg|png)$/, loader: 'sizeof-loader' }
    ]
  },
  plugins: [
    HtmlWebpackPluginConfig,
    new webpack.DefinePlugin({
      __ZESJE_VERSION__: JSON.stringify(zesjeVersion)
    })
  ]
}
