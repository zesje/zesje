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
      { test: /\.css$/, use: [{ loader: "style-loader" }, { loader: "css-loader" }] },
      { test: /\.(png|jpg|gif)$/, loader: "file-loader" },
      { test: /\.woff2?(\?v=[0-9]\.[0-9]\.[0-9])?$/, loader: "url-loader" },
      { test: /\.(ttf|eot|svg)(\?[\s\S]+)?$/, loader: "file-loader" },
    ]
  },

  plugins: [HtmlWebpackPluginConfig],

  devServer: {
    hot: true,
    proxy: {
      '/api': {
        target: 'http://localhost:5000'
      }
    },
    historyApiFallback: true,
    port: 8881,
    publicPath: '/',
    host: '0.0.0.0',
    overlay: {
      warnings: true,
      errors: true
    },
    watchContentBase: true,
    watchOptions: {
      poll: true
    }
  }
}
