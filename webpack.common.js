/*
    ./webpack.config.js
*/
const path = require('path');

const HtmlWebpackPlugin = require('html-webpack-plugin');
const HtmlWebpackPluginConfig = new HtmlWebpackPlugin({
  template: './client/index.html',
  favicon: './client/favicon.ico',
  filename: 'index.html',
  inject: 'body'
})

module.exports = {
  entry: './client/index.js',
  output: {
    path: path.resolve('zesje/static'),
    filename: 'index_bundle.js'
  },
  module: {
    loaders: [
      { test: /\.(jsx|js)$/, loader: 'babel-loader', exclude: /node_modules/ },
      { test: /\.(png|jpg|gif)$/, loader: "file-loader" },
      { test: /\.(woff(2)?|ttf|eot|svg|otf)(\?v=\d+\.\d+\.\d+)?$/, loader: "file-loader" },
      { test: /\.(md)$/, loader: "raw-loader" },
    ]
  },

  plugins: [HtmlWebpackPluginConfig]
  }
