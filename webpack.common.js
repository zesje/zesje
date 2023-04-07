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
    globalObject: 'this',
    // NodeJS 17 compatibility: https://stackoverflow.com/a/73027407/2214847
    hashFunction: 'xxhash64'
  },
  module: {
    rules: [
      { test: /\.(jsx|js)$/, loader: 'babel-loader', options: { cacheDirectory: true }, exclude: /node_modules/ },
      { test: /\.(woff(2)?|ttf|eot|svg|otf)(\?v=\d+\.\d+\.\d+)?$/, type: 'asset/resource' },
      { test: /\.md$/, use: [{ loader: 'html-loader' }, { loader: 'markdown-loader' }] },
      { test: /\.png$/, loader: path.resolve('client/sizeof_loader.js'), dependency: { not: ['url'] } },
      { test: /\.(gif|jpeg|jpg)$/, type: 'asset/resource' }
    ]
  },
  plugins: [
    HtmlWebpackPluginConfig,
    new webpack.DefinePlugin({
      __ZESJE_VERSION__: JSON.stringify(zesjeVersion)
    })
  ],
  resolve: {
    extensions: ['.ts', '.js'],
    fallback: {
      // Webpack 5 + Nodejs 17+ compatibility: https://github.com/diegomura/react-pdf/issues/1029
      buffer: require.resolve('buffer')
    }
  }
}
