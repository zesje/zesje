import React from 'react'
import Switch from 'react-bulma-switch/full'

/**
 * PanelMCQ is a component that allows the user to generate mcq options
 */
class PanelMCQ extends React.Component {
  constructor (props) {
    super(props)
    this.onChangeNPA = this.onChangeNPA.bind(this)
    this.onChangeLabelType = this.onChangeLabelType.bind(this)
    this.generateLabels = this.generateLabels.bind(this)

    this.state = {
      isMCQ: false,
      chosenLabelType: 0,
      nrPossibleAnswers: 1,
      labelTypes: ['None', 'True/False', 'A, B, C ...', '1, 2, 3 ...']
    }
  }

  static getDerivedStateFromProps (newProps, prevState) {
    if (prevState.problemId !== newProps.problem.id) {
      let prob = newProps.problem
      return {
        problemId: prob.id,
        isMCQ: prob.mc_options.length > 0,
        nrPossibleAnswers: prob.mc_options.length || 1,
        chosenLabelType: prob.labelType || PanelMCQ.deriveLabelType(prob),
      }
    }

    return null;
  }

  static deriveLabelType (prob) {
    let options = prob.mc_options
    if (options.length === 0) {
      prob.labelType = 0
    } else if (options.length === 2 && ((options[0].label === 'T' && options[1].label === 'F')
      || (options[0].label === 'F' && options[1].label === 'T'))) {
      prob.labelType = 1
    } else if (options[0].label.match(/[a-z]/)) {
      prob.labelType = 2
    } else if (parseInt(options[0].label)) {
      prob.labelType = 3
    } else {
      prob.labelType = 0
    }

    return prob.labelType
  }



  // this function is called when the input is changed for the number of possible answers
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

  // this function is called when the input is changed for the desired label type
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

  /**
   * This function generates an array with the labels for each option
   * @param nrLabels the number of options that need to be generated
   * @returns {any[]|string[]|number[]}
   */
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

  /**
   * This function renders the panel with the inputs for generating multiple choice options
   * @returns the react component containing the mcq panel
   */
  render () {
    return (
      <nav className='panel'>
        <p className='panel-heading'>
          Multiple Choice Question
        </p>
        <div className='panel-block'>
          <div className='field'>
            <label className='label'> Multiple choice question </label>
            <Switch color='info' outlined value={this.props.problem.mc_options.length > 0} onChange={(e) => {
              if (e.target.checked) {
                let npa = this.state.nrPossibleAnswers
                let labels = this.generateLabels(npa)
                this.props.onGenerateBoxesClick(labels)
              } else {
                this.props.onDeleteBoxesClick()
              }
            }} />
          </div>
        </div>
        <div className='panel-block'>
          <div className='field'>
            <React.Fragment>
              <label className='label'>Number possible answers</label>
              <div className='control'>
                <input type='number'  value={this.state.nrPossibleAnswers} min='1'
                       max={this.props.totalNrAnswers} className='input' onChange={this.onChangeNPA} />
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
      </nav>
    )
  }
}

export default PanelMCQ
