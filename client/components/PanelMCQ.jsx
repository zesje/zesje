import React from 'react'
import Switch from 'react-bulma-switch/full'
import './PanelMCQ.css'

const LABEL_TYPES = {
  NONE: 0, // No labels
  TRUE_FALSE: 1, // True or false
  LETTERS: 2, // A, B, C, ...
  NUMERIC: 3 // 1, 2, 3, ...
}

const LABEL_TYPE_STRINGS = ['None', 'True/False', 'A, B, C ...', '1, 2, 3 ...']

/**
 * PanelMCQ is a component that allows the user to generate mc questions and options
 */
class PanelMCQ extends React.Component {
  constructor (props) {
    super(props)

    this.state = {
      chosenLabelType: LABEL_TYPES.LETTERS,
      nrPossibleAnswers: 2
    }
  }

  // modify the state if the properties are changed
  static getDerivedStateFromProps (newProps, prevState) {
    // if another problem is selected, update the state and implicitly the contents of the inputs
    if (prevState.problemId !== newProps.problem.id) {
      let prob = newProps.problem
      return {
        problemId: prob.id,
        nrPossibleAnswers: prob.mc_options.length || 2,
        chosenLabelType: PanelMCQ.deriveLabelType(prob.mc_options)
      }
    }

    return null
  }

  /**
   * Derive the label type given an array of options.
   * @param options the options that correspond to a problem
   * @returns {number} the index in the labelTypes array representing the label type
   */
  static deriveLabelType (options) {
    if (options.length === 0) {
      return LABEL_TYPES.LETTERS
    } else if (options.length === 2 && ((options[0].label === 'T' && options[1].label === 'F') ||
      (options[0].label === 'F' && options[1].label === 'T'))) {
      return LABEL_TYPES.TRUE_FALSE
    } else if (options[0].label.match(/[A-Z]/)) {
      return LABEL_TYPES.LETTERS
    } else if (parseInt(options[0].label)) {
      return LABEL_TYPES.NUMERIC
    } else {
      return LABEL_TYPES.NONE
    }
  }

  /**
   * Check if a change is currently in progress.
   * @returns {boolean} true if there's a change operation in progress, false otherwise
   */
  operationInProgress = () => {
    let prob = this.props.problem
    return this.state.chosenLabelType !== PanelMCQ.deriveLabelType(prob.mc_options) ||
      this.state.nrPossibleAnswers !== prob.mc_options.length
  }

  // this functions calculates
  updateNumberOptions = () => {
    let difference = this.state.nrPossibleAnswers - this.props.problem.mc_options.length
    if (difference > 0) {
      let startingAt = this.props.problem.mc_options.length
      let labels = this.generateLabels(difference, startingAt)
      return this.props.generateMCOs(labels)
    } else if (difference < 0) {
      return this.props.deleteMCOs(-difference)
    }

    return Promise.resolve(true)
  }

  // this function is called when the input is changed for the number of possible answers
  onChangeNPA = (e) => {
    if (this.operationInProgress()) return // finish the first operation first to ensure consistency

    let value = parseInt(e.target.value)
    if (!isNaN(value) && value <= this.props.totalNrAnswers) {
      if (this.state.chosenLabelType === LABEL_TYPES.TRUE_FALSE) {
        value = 2
      }
      this.setState({
        nrPossibleAnswers: value
      }, this.updateNumberOptions)
    }
  }

  // this function is called when the input is changed for the desired label type
  onChangeLabelType = (e) => {
    if (this.operationInProgress()) return // finish the first operation first to ensure consistency

    let value = parseInt(e.target.value)
    if (!isNaN(value)) {
      // if the label type is True/False then reduce the number of mc options to 2
      if (parseInt(value) === LABEL_TYPES.TRUE_FALSE) {
        this.setState({
          nrPossibleAnswers: 2,
          chosenLabelType: value
        }, () => {
          let labels = this.generateLabels(this.state.nrPossibleAnswers, 0)
          this.updateNumberOptions().then(() => this.props.updateLabels(labels))
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
  generateLabels = (nrLabels, startingAt) => {
    let type = this.state.chosenLabelType

    switch (type) {
      case LABEL_TYPES.TRUE_FALSE:
        return ['T', 'F'].slice(startingAt)
      case LABEL_TYPES.LETTERS:
        return Array.from(Array(nrLabels).keys()).map(
          (e) => String.fromCharCode(e + 65 + startingAt))
      case LABEL_TYPES.NUMERIC:
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
        <div className='panel-block mcq-block'>
          <label className='label'> Multiple choice </label>
          <Switch color='info' outlined value={this.props.problem.mc_options.length > 0} onChange={(e) => {
            if (e.target.checked) {
              let npa = this.state.nrPossibleAnswers
              let labels = this.generateLabels(npa, 0)
              this.props.generateMCOs(labels)
            } else {
              this.props.deleteMCOs(this.props.problem.mc_options.length)
            }
          }} />
        </div>
        { this.props.problem.mc_options.length > 0 ? (
          <React.Fragment>
            <div className='panel-block mcq-block'>
              <div className='inline-mcq-edit'>
                <label>#</label>
                <input type='number' value={this.state.nrPossibleAnswers} min='1'
                  max={this.props.totalNrAnswers} className='input' onChange={this.onChangeNPA} />
              </div>
              <div className='inline-mcq-edit'>
                <label>Labels</label>
                <div className='select is-hovered is-fullwidth'>
                  <div className='select is-hovered is-fullwidth'>
                    <select value={this.state.chosenLabelType} onChange={this.onChangeLabelType}>
                      {
                        LABEL_TYPE_STRINGS.map((label, i) => <option key={i} value={String(i)}>{label}</option>)
                      }
                    </select>
                  </div>
                </div>
              </div>
            </div>
          </React.Fragment>) : null
        }
      </React.Fragment>
    )
  }
}

export default PanelMCQ
