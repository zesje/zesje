const merge = require('webpack-merge');
const common = require('./webpack.common.js');

module.exports = merge(common, {
    module: {
        loaders: [
          { test: /\.css$/, use: [ 'style-loader', 'css-loader' ]}
        ]
    },

    devtool: 'eval-source-map',

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
    }
})