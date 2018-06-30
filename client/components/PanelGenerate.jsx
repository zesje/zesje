import React from 'react'

import * as api from '../api.jsx'

class PanelGenerate extends React.Component {
    types = [
      'ZIP',
      'PDF'
    ]

    state = {
      copyRangeStart: 1,
      copyRangeEnd: '',
      type: this.types[0],
      valid: false,
      editing: true,
      isGenerating: false,
      isGenerated: false
    }

    pageNumberOrEmpty = new RegExp(/^([1-9]+\d*)?$/)

    validate = () => {
      if (parseInt(this.state.copyRangeStart) <= parseInt(this.state.copyRangeEnd)) {
        this.setState({
          valid: true,
          editing: false
        })
      } else {
        this.setState({
          valid: false,
          editing: false
        })
      }
    }

    inputColor = () => {
      if (this.state.editing) {
        return ''
      } else if (this.state.valid) {
        return 'is-success'
      } else {
        return 'is-danger'
      }
    }

    onClickGenerate = () => {
      if (this.state.valid) {
        const postData = {
          copies_start: this.state.copyRangeStart,
          copies_end: this.state.copyRangeEnd
        }
        const type = this.state.type
        this.setState({
          isGenerating: true
        }, () => {
          api.post('exams/' + this.props.examID + '/generated_pdfs', postData)
            .then(() => {
              this.setState({
                isGenerating: false,
                isGenerated: true
              })
            })
        })
      } else {
        alert('Insert proper range')
      }
    }

    renderInput = (props) => {
      return <input
        className={'input ' + this.inputColor()}
        type='text'
        placeholder={props.placeholder}
        maxLength={4}
        style={props.style}
        value={props.value}
        onFocus={() => this.setState({ editing: true })}
        onBlur={() => this.validate()}
        onChange={(e) => {
          if (this.pageNumberOrEmpty.test(e.target.value)) {
            this.setState({
              [props.valueKey]: e.target.value,
              isGenerated: false,
              isGenerating: false
            }, () => {
              this.validate()
            })
          }
        }}
      />
    }

    render = () => {
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
                {this.renderInput({
                  placeholder: 'start',
                  style: { textAlign: 'right' },
                  value: this.state.copyRangeStart,
                  valueKey: 'copyRangeStart'
                })}
              </p>
              <p className='control'>
                <a className='button is-static'>
                                -
                </a>
              </p>
              <p className='control is-expanded'>
                {this.renderInput({
                  placeholder: 'end',
                  style: { textAlign: 'left' },
                  value: this.state.copyRangeEnd,
                  valueKey: 'copyRangeEnd'
                })}
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
                  <select
                    onChange={(e) => {
                      this.setState({
                        type: e.target.value
                      })
                    }}
                  >
                    {this.types.map((type, index) => {
                      return <option key={'key_' + index}>{type}</option>
                    })}
                  </select>
                </span>
              </p>
              <p className='control'>
                <button
                  className={'button is-expanded is-link' + (this.state.isGenerating ? ' is-loading' : '')}
                  onClick={this.onClickGenerate}
                  disabled={!this.state.valid || this.state.isGenerated}
                >
                                Generate
                </button>
              </p>
              <p className='control'>
                <a
                  className={'button is-expanded is-link'}
                  href={this.state.isGenerated ? ('/api/exams/' + this.props.examID +
                                    '/generated_pdfs' +
                                    '?type=' + this.state.type.toLowerCase() +
                                    '&copies_start=' + parseInt(this.state.copyRangeStart) +
                                    '&copies_end=' + parseInt(this.state.copyRangeEnd)) : null}
                  disabled={!this.state.isGenerated}
                >
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
