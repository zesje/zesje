import React from 'react'

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

  renderInput = (props) => {
    // Hardcode the width since Bulma does not support the size attribute
    props.style['width'] = '3.5em'
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
          <div className='field is-grouped'>
            <div className='field has-addons is-marginless'>
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
              <p className='control'>
                {this.renderInput({
                  placeholder: 'end',
                  style: { textAlign: 'left' },
                  value: this.state.copyRangeEnd,
                  valueKey: 'copyRangeEnd'
                })}
              </p>
            </div>
            <div className='field has-addons' style={{ marginLeft: '1em' }}>
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
                <a
                  className={'button is-expanded is-link'}
                  href={'/api/exams/' + this.props.examID +
                    '/generated_pdfs' +
                    '?type=' + this.state.type.toLowerCase() +
                    '&copies_start=' + parseInt(this.state.copyRangeStart) +
                    '&copies_end=' + parseInt(this.state.copyRangeEnd)}
                >
                  <span className='icon is-small'>
                    <i className='fa fa-download' />
                  </span>
                </a>
              </p>
            </div>
          </div>
        </div>
      </nav>
    )
  }
}

export default PanelGenerate
