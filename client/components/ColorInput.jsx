import React from 'react'

class ColorInput extends React.Component {
  state = {
    editing: true
  }

  onStartEditing = () => this.setState({ editing: true })
  onFinishEditing = () => this.setState({ editing: false })

  inputColor = (value) => {
    if (this.state.editing) {
      return ''
    } else if (value) {
      return 'is-success'
    } else {
      return 'is-danger'
    }
  }

  render () {
    return (
      <input
        className={'input ' + this.inputColor(this.props.value)}
        onFocus={this.onStartEditing}
        onBlur={this.onFinishEditing}
        {...this.props}
      />
    )
  }
}

export default ColorInput
