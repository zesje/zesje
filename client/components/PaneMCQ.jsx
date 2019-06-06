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
    this.updateNumberOptions = this.updateNumberOptions.bind(this)

    this.state = {
      isMCQ: false,
      chosenLabelType: 2,
      nrPossibleAnswers: 2,
      labelTypes: ['None', 'True/False', 'A, B, C ...', '1, 2, 3 ...']
    }
  }

  static getDerivedStateFromProps (newProps, prevState) {
    if (prevState.problemId !== newProps.problem.id) {
      let prob = newProps.problem
      return {
        problemId: prob.id,
        isMCQ: prob.mc_options.length > 0,
        nrPossibleAnswers: prob.mc_options.length || 2,
        chosenLabelType: PanelMCQ.deriveLabelType(prob.mc_options),
      }
    }

    return null;
  }

  static deriveLabelType (options) {
    if (options.length === 0) {
      return 2
    } else if (options.length === 2 && ((options[0].label === 'T' && options[1].label === 'F')
      || (options[0].label === 'F' && options[1].label === 'T'))) {
      return 1
    } else if (options[0].label.match(/[A-Z]/)) {
      return 2
    } else if (parseInt(options[0].label)) {
      return 3
    } else {
      return 0
    }
  }

  updateNumberOptions() {
    let difference = this.state.nrPossibleAnswers - this.props.problem.mc_options.length
    if (difference > 0) {
      let startingAt = this.props.problem.mc_options.length
      let labels = this.generateLabels(difference, startingAt)
      return this.props.generateMCOs(labels)
    } else if (difference < 0) {
      return this.props.deleteMCOs(-difference)
    }
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
      }, this.updateNumberOptions)
    }
  }

  // this function is called when the input is changed for the desired label type
  onChangeLabelType (e) {
    let value = parseInt(e.target.value)
    if (!isNaN(value)) {
      if (parseInt(value) === 1) {
        this.setState({
          nrPossibleAnswers: 2,
          chosenLabelType: value
        }, () => {
          this.updateNumberOptions()
          let labels = this.generateLabels(this.state.nrPossibleAnswers, 0)
          this.props.updateLabels(labels)
        })
      } else {
        this.setState({
          chosenLabelType: value
        }, () => {
          let labels = this.generateLabels(this.state.nrPossibleAnswers, 0)
          this.props.updateLabels(labels)
        })
      }
    }
  }

  /**
   * This function generates an array with the labels for each option
   * @param nrLabels the number of options that need to be generated
   * @param startingAt at which number/character to start generating labels
   * @returns {any[]|string[]|number[]}
   */
  generateLabels (nrLabels, startingAt) {
    let type = this.state.chosenLabelType

    switch (type) {
      case 1:
        return ['T', 'F']
      case 2:
        return Array.from(Array(nrLabels).keys()).map(
          (e) => String.fromCharCode(e + 65 + startingAt))
      case 3:
        return Array.from(Array(nrLabels).keys()).map(e => String(e + 1 + startingAt))
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
      <React.Fragment>
        <div className='panel-block'>
          <div className='field'>
            <label className='label'> Multiple choice question </label>
            <Switch color='info' outlined value={this.props.problem.mc_options.length > 0} onChange={(e) => {
              this.setState({
                isMCQ: true
              })
              if (e.target.checked) {
                let npa = this.state.nrPossibleAnswers
                let labels = this.generateLabels(npa, 0)
                this.props.generateMCOs(labels)
              } else {
                this.props.deleteMCOs(this.props.problem.mc_options.length)
              }
            }} />
            { this.state.isMCQ ? (
              <React.Fragment>
                <label>Number options</label>
                <div className='control'>
                  <input type='number'  value={this.state.nrPossibleAnswers} min='1'
                         max={this.props.totalNrAnswers} className='input' onChange={this.onChangeNPA} />
                </div>
                <label>Labels</label>
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
              </React.Fragment>) : null
            }
          </div>
        </div>
      </React.Fragment>
    )
  }
}

export default PanelMCQ
