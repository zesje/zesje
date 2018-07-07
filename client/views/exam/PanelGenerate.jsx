import React from 'react'

import * as api from '../../api.jsx'

const RangeInput = (props) => {
  return <input
    className={'input' + props.color}
    type='text'
    placeholder={props.placeholder}
    maxLength={4}
    style={{
      textAlign: props.align
    }}
    value={props.value}
    name={props.name}
    onChange={props.onChange}
  />
}

class PanelGenerate extends React.Component {
  static types = [
    'ZIP',
    'PDF'
  ]
  state = {
    copyRangeStart: 1,
    copyRangeEnd: '',
    type: PanelGenerate.types[0],
    valid: false,
    edited: false,
    isGenerating: false,
    isGenerated: false
  }

  static pageNumberOrEmpty = new RegExp(/^([1-9]+\d*)?$/)
  onChangeRange = (event) => {
    const value = event.target.value
    if (PanelGenerate.pageNumberOrEmpty.test(value)) {
      this.setState({
        [event.target.name]: value,
        isGenerated: false,
        isGenerating: false,
        edited: true
      }, () => this.setState(prevState => ({
        valid: parseInt(prevState.copyRangeStart) <= parseInt(prevState.copyRangeEnd)
      })))
    }
  }

  onSelect = (event) => {
    this.setState({
      type: event.target.value
    })
  }

  onClickGenerate = () => {
    if (!this.state.valid) {
      alert('Insert proper range')
      return
    }

    const postData = {
      copies_start: this.state.copyRangeStart,
      copies_end: this.state.copyRangeEnd
    }
    this.setState({
      isGenerating: true
    })
    api.post('exams/' + this.props.examID + '/generated_pdfs', postData)
      .then(() => {
        this.setState({
          isGenerating: false,
          isGenerated: true
        })
      })
  }

  render = () => {
    const inputColor = !this.state.edited ? '' : (this.state.valid ? ' is-success' : ' is-danger')

    return (
      <nav className='panel'>
        <p className='panel-heading'>
          Download exam
        </p>
        <div className='panel-block'>
          <label className='label'>Copy number range</label>
        </div>
        <div className='panel-block'>
          <div className='field has-addons' style={{ maxWidth: '11em' }}>
            <p className='control'>
              <RangeInput placeholder='start' align='right' color={inputColor} onChange={this.onChangeRange}
                value={this.state.copyRangeStart} name='copyRangeStart' />
            </p>
            <p className='control'>
              <a className='button is-static'>
                -
              </a>
            </p>
            <p className='control is-expanded'>
              <RangeInput placeholder='end' align='left' color={inputColor} onChange={this.onChangeRange}
                value={this.state.copyRangeEnd} name='copyRangeEnd' />
            </p>
          </div>
        </div>
        <div className='panel-block'>
          <label className='label'>Generate and download</label>
        </div>
        <div className='panel-block'>
          <div className='field has-addons'>
            <p className='control'>
              <span className='select'>
                <select onChange={this.onSelect} >
                  {PanelGenerate.types.map((type, index) => {
                    return <option key={'key_' + index}>{type}</option>
                  })}
                </select>
              </span>
            </p>
            <p className='control'>
              <button
                className={'button is-expanded is-link' + (this.state.isGenerating ? ' is-loading' : '')}
                onClick={this.onClickGenerate}
                disabled={!this.state.valid || this.state.isGenerated} >
                Generate
              </button>
            </p>
            <p className='control'>
              <a
                className={'button is-expanded is-link'}
                href={this.state.isGenerated
                  ? ('/api/exams/' + this.props.examID +
                  '/generated_pdfs' +
                  '?type=' + this.state.type.toLowerCase() +
                  '&copies_start=' + parseInt(this.state.copyRangeStart) +
                  '&copies_end=' + parseInt(this.state.copyRangeEnd))
                  : undefined}
                disabled={!this.state.isGenerated} >
                Download
              </a>
            </p>
          </div>
        </div>
      </nav>
    )
  }
}

export default PanelGenerate
