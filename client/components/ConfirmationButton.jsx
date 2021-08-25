import React from 'react'

import ConfirmationModal from './ConfirmationModal.jsx'

class ConfirmationButton extends React.Component {
  state = {
    confirming: false
  }

  render () {
    return (
      <>
        <button
          className={this.props.className}
          disabled={this.props.disabled}
          onClick={() => this.setState({ confirming: true })}
        >
          {this.props.children}
        </button>
        <ConfirmationModal
          active={this.state.confirming}
          color='is-danger'
          headerText={this.props.confirmationText}
          contentText={this.props.contentText}
          confirmText={this.props.children}
          onCancel={() => this.setState({ confirming: false })}
          onConfirm={() => {
            this.setState({
              confirming: false
            }, () => this.props.onConfirm())
          }}
        />
      </>
    )
  }
}

export default ConfirmationButton
