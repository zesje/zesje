import React from 'react'
import Mousetrap from 'mousetrap'

function withShortcuts (WrappedComponent) {
  return class extends React.Component {
    displayName: 'ShortcutBinder'

    boundShortcuts = []

    componentWillUnmount = () => {
      this.unbindAllShortcuts()
    }

    bindShortcut = (keys, callback, type) => {
      Mousetrap.bind(keys, callback, type)
      this.boundShortcuts.push({ keys: keys, type: type })
    }

    unbindAllShortcuts = () => {
      this.boundShortcuts.forEach(shortcut => Mousetrap.unbind(shortcut.keys, shortcut.type))
      this.boundShortcuts = []
    }

    render () {
      return <WrappedComponent bindShortcut={this.bindShortcut} {...this.props} />
    }
  }
}

export default withShortcuts
