// Based on: https://github.com/boopathi/image-size-loader/issues/10#issue-237059548

const sizeOf = require('image-size')

module.exports = function (content) {
  this.cacheable && this.cacheable()

  const resourcePath = this.resourcePath
  const image = sizeOf(content)
  const bytes = this.fs.statSync(resourcePath).size

  const name = resourcePath.slice(resourcePath.lastIndexOf('/') + 1)
  this.emitFile(name, content)

  return `
    module.exports = {
      src: "${name}",
      width: ${JSON.stringify(image.width)},
      height: ${JSON.stringify(image.height)},
      type: ${JSON.stringify(image.type)},
      bytes: ${JSON.stringify(bytes)},

      toString: function() {
        return "${name}";
      }
    };
  `
}

module.exports.raw = true
