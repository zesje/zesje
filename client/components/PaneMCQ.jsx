import React from 'react'

class PanelMCQ extends React.Component {
  constructor (props) {
    super(props)
    this.onChangeNPA = this.onChangeNPA.bind(this)
    this.onChangeLabelType = this.onChangeLabelType.bind(this)
    this.generateLabels = this.generateLabels.bind(this)
    this.state = {
      chosenLabelType: 0,
      nrPossibleAnswers: 2,
      labelTypes: ['None', 'True/False', 'A, B, C ...', '1, 2, 3 ...']
    }
  }
  onChangeNPA (e) {
    let value = parseInt(e.target.value)
    if (!isNaN(value)) {
      if (this.state.chosenLabelType === 1) {
        value = 2
      }
      this.setState({
        nrPossibleAnswers: value
      })
    }
  }

  onChangeLabelType (e) {
    let value = parseInt(e.target.value)
    if (!isNaN(value)) {
      this.setState({
        chosenLabelType: value
      })
      if (parseInt(value) === 1) {
        this.setState({
          nrPossibleAnswers: 2
        })
      }
    }
  }

  generateLabels (nrLabels) {
    let type = this.state.chosenLabelType

    switch (type) {
      case 1:
        return ['T', 'F']
      case 2:
        return Array.from(Array(nrLabels).keys()).map((e) => String.fromCharCode(e + 65))
      case 3:
        return Array.from(Array(nrLabels).keys()).map(e => e + 1)
      default:
        return Array(nrLabels).fill(' ')
    }
  }

  render () {
    return (
      <nav className='panel'>
        <p className='panel-heading'>
          Multiple Choice Question
        </p>
        <div className='panel-block'>
          <div className='field'>
            <React.Fragment>
              <label className='label'>Number possible answers</label>
              <div className='control'>
                {(function () {
                  var optionList = []
                  for (var i = 1; i <= this.props.totalNrAnswers; i++) {
                    const optionElement = <option key={i} value={String(i)}>{i}</option>
                    optionList.push(optionElement)
                  }
                  return (<div className='select is-hovered is-fullwidth'>
                    <select value={this.state.nrPossibleAnswers} onChange={this.onChangeNPA}>{optionList}</select>
                  </div>)
                }.bind(this)())}
              </div>
            </React.Fragment>
          </div>
        </div>
        <div className='panel-block'>
          <div className='field'>
            <React.Fragment>
              <label className='label'>Answer boxes labels</label>
              <div className='control'>
                <div className='select is-hovered is-fullwidth'>
                  {(function () {
                    var optionList = this.state.labelTypes.map(
                      (label, i) => <option key={i} value={String(i)}>{label}</option>
                    )
                    return (
                      <div className='select is-hovered is-fullwidth'>
                        <select value={this.state.chosenLabelType} onChange={this.onChangeLabelType}>
                          {optionList}
                        </select>
                      </div>
                    )
                  }.bind(this)())}
                </div>
              </div>
            </React.Fragment>
          </div>
        </div>
        <div className='panel-block'>
          <div className='field'>
            <label className='label'>
              <input type='checkbox' checked={this.props.renderSeparately} onChange={
                (e) => {
                  this.props.onRenderOptionChange(e.target.checked)
                }} />
                Render options separately
            </label>
          </div>
        </div>
        <div className='panel-block field is-grouped'>
          <button
            disabled={this.props.disabledGenerateBoxes}
            className='button is-link is-fullwidth'
            onClick={() => {
              let npa = this.state.nrPossibleAnswers
              let labels = this.generateLabels(npa)
              this.props.onGenerateBoxesClick(labels)
            }}
          >
            Generate
          </button>
          <button
            disabled={this.props.disabledDeleteBoxes}
            className='button is-danger is-fullwidth'
            onClick={() => {
              console.log('Delete button not yet implemented.')
            }}
          >
            Delete
          </button>
        </div>
      </nav>
    )
  }
}

export default PanelMCQ
