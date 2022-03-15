import React from 'react'

export const Spinner = ({ color }) => (
  <p className='container has-text-centered'>
    <span className={'icon is-large has-text-' + (color != null ? color : 'info')}>
      <i className="fas fa-spinner fa-2x fa-pulse"></i>
    </span>
  </p>
)

class Img extends React.Component {
  state = {
    status: 'loading'
  }

  static getDerivedStateFromProps (nextProps, prevState) {
    if (prevState.src !== nextProps.src) {
      return {
        src: nextProps.src || '',
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
    return <>
      <img src={this.state.src}
        onLoad={this.onLoad}
        onError={this.onError}
        style={{ display: this.state.status !== 'success' ? 'none' : '' }}
        {...this.props.imgProps} />
      {this.state.status === 'loading' ? <Spinner color={this.props.color} /> : null}
      {this.state.status === 'error' ? this.props.errorElement : null}
    </>
  }
}

export default Img
