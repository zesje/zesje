import React from 'react'

import Spinner from './Spinner.jsx'

class Img extends React.Component {
  state = {
    status: 'loading'
  }

  static getDerivedStateFromProps (nextProps, prevState) {
    if (prevState.src !== nextProps.src) {
      return {
        src: nextProps.src,
        status: nextProps.src != null ? 'loading' : 'error'
      }
    }

    return null
  }

  onLoad = () => {
    this.setState({ status: 'success' })
  }

  onError = () => {
    this.setState({ status: 'error' })
  }

  render () {
    const { src, color, error, ...imgProps } = this.props

    return <>
      <img src={this.state.src}
        onLoad={this.onLoad}
        onError={this.onError}
        style={{ display: this.state.status !== 'success' ? 'none' : '' }}
        {...imgProps} />
      {this.state.status === 'loading' ? <Spinner color={color} /> : null}
      {this.state.status === 'error' ? error : null}
    </>
  }
}

export default Img
