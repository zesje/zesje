import React from 'react'
import { Link } from 'react-router-dom'

import './NavBar.css'
import * as api from '../api.jsx'
import 'bulma-tooltip/dist/css/bulma-tooltip.min.css'

import HelpModal from './help/HelpModal.jsx'
import shortcutsMarkdown from './help/ShortcutsHelp.md'
import gradingPolicyMarkdown from './help/GradingPolicyHelp.md'

const BurgerButton = (props) => (
  <button className={'button navbar-burger' + (props.foldOut ? ' is-active' : '')}
    onClick={props.burgerClick}>
    <span />
    <span />
    <span />
  </button>
)

const TooltipLink = (props) => {
  let pred = props.predicate.find(pred => pred[0])
  if (!pred) pred = [false, null]

  return <div className={'navbar-item no-padding' + (pred[0] ? ' tooltip is-tooltip-bottom' : '')}
    data-tooltip={pred[1]}>
    <Link className='navbar-item' disabled={pred[0]} to={props.to}> { props.text } </Link>
  </div>
}

const ExamDropdown = (props) => {
  return (<div className='navbar-item has-dropdown is-hoverable'>
    <Link className='navbar-link' to={'/exams/' + (props.selectedExam ? props.selectedExam.id : '')}>
      {props.selectedExam ? <i>{props.selectedExam.name}</i> : 'Add exam'}
    </Link>
    <div className='navbar-dropdown'>
      {props.list.map((exam) => (
        <Link className={'navbar-item' + (props.selectedExam && props.selectedExam.id === exam.id ? ' is-active' : '')}
          to={'/exams/' + exam.id} key={exam.id} >
          <i>{exam.name}</i>
        </Link>
      ))}
      <hr className='navbar-divider' />
      <Link className='navbar-item' to={'/exams'} >
        Add new
      </Link>
    </div>
  </div>)
}

const GraderDropdown = (props) => (
  <div className='navbar-item has-dropdown is-hoverable'>
    <div className='navbar-link' >
      {props.grader ? <i>{props.grader.name}</i> : 'Select grader'}
    </div>
    <div className='navbar-dropdown'>
      {props.list.map((grader) => (
        <a className={'navbar-item' + (props.grader && props.grader.id === grader.id ? ' is-active' : '')}
          key={grader.id} onClick={() => props.changeGrader(grader)} >
          <i>{grader.name}</i>
        </a>
      ))}
      <hr className='navbar-divider' />
      <Link className='navbar-item' to={'/graders'} >
        Add grader
      </Link>
    </div>
  </div>
)

const ExportDropdown = (props) => {
  const exportFormats = [
    { label: 'Excel Spreadsheet', format: 'xlsx' },
    { label: 'Detailed Excel Spreadsheet', format: 'xlsx_detailed' },
    { label: 'Pandas Dataframe', format: 'dataframe' },
    { label: 'Zip of (anonymized) pdf files', format: 'pdf' }
  ]

  const exportUrl = format => `/api/export/${format}/${props.examID}`

  return (
    <div className='navbar-item has-dropdown is-hoverable' >
      <div className='navbar-link'>
        Export
      </div>
      <div className='navbar-dropdown'>
        {exportFormats.map((exportFormat, i) =>
          <a className='navbar-item'
            href={exportUrl(exportFormat.format)}
            disabled={props.disabled}
            key={i}>
            {exportFormat.label}
          </a>
        )}
        <hr className='navbar-divider' />
        <a className='navbar-item'
          href={'/api/export/graders/' + props.examID}
          disabled={props.disabled}>
          Export grader statistics
        </a>
        <hr className='navbar-divider' />
        <a className='navbar-item' href='/api/export/full'>
          Export full database
        </a>
      </div>
    </div>
  )
}

class NavBar extends React.Component {
  pages = {
    shortcuts: { title: 'Shortcuts', content: shortcutsMarkdown },
    gradingPolicy: { title: 'Auto-approve', content: gradingPolicyMarkdown }
  }

  state = {
    foldOut: false,
    examList: [],
    graderList: [],
    helpPage: null,
    examID: null
  }

  componentDidUpdate = (prevProps, prevState) => {
    if (prevProps.examID !== this.props.examID) {
      this.setState({examID: this.props.examID})
    }
  }

  componentDidMount = () => {
    this.updateExamList()
    this.updateGraderList()
  }

  updateExamList = () => {
    api.get('exams')
      .then(exams => {
        this.setState(prevState => ({
          examList: exams,
          examID: prevState.examID || (exams.length > 1 ? exams[exams.length - 1].id : null)
        }))
      })
  }

  updateGraderList = () => {
    api.get('graders')
      .then(graders => {
        this.setState({
          graderList: graders
        })

        const oldGraderID = parseInt(window.sessionStorage.getItem('graderID'))
        if (oldGraderID >= 0) {
          const i = graders.findIndex(grader => grader.id === oldGraderID)
          if (this.props.grader === null && i >= 0) this.props.changeGrader(graders[i])
        }
      })
  }

  burgerClick = () => {
    this.setState({
      foldOut: !this.state.foldOut
    })
  }

  setHelpPage = (helpPage) => {
    this.setState({ helpPage: helpPage })
  }

  render () {
    const selectedExam = this.state.examList.find(exam => exam.id === this.state.examID)

    const predicateNoExam = [selectedExam === null || selectedExam === undefined,
      'No exam selected.']
    const predicateExamNotFinalized = [!predicateNoExam[0] && !selectedExam.finalized,
      'The exam is not finalized yet.']
    const predicateSubmissionsEmpty = [!predicateNoExam[0] && selectedExam.submissions.length === 0,
      'There are no submissions, please upload some.']
    const predicateNoGraderSelected = [this.props.grader === null,
      'Please select a grader.']

    return (
      <nav className='navbar' role='navigation' aria-label='dropdown navigation'>

        <div className='navbar-brand'>
          <div className='navbar-item has-text-info'>
            <span className='icon is-medium'>
              <i className='fa fa-edit fa-2x' />
            </span>
          </div>

          <Link className='navbar-item has-text-info' to='/'><b>Zesje</b></Link>
          <div className='navbar-item' />

          <BurgerButton foldOut={this.props.foldOut} burgerClick={this.burgerClick} />
        </div>

        <div className={'navbar-menu' + (this.state.foldOut ? ' is-active' : '')} onClick={this.burgerClick}>
          <div className='navbar-start'>

            {this.state.examList.length
              ? <ExamDropdown selectedExam={selectedExam} list={this.state.examList} />
              : <Link className='navbar-item' to='/exams'>Add exam</Link>
            }

            <TooltipLink
              to={'/scans/' + this.props.examID}
              text='Scans'
              predicate={[predicateNoExam, predicateExamNotFinalized]} />
            <Link className='navbar-item' to={'/students/' + this.props.examID}>Students</Link>
            <TooltipLink
              to={'/grade/' + this.props.examID}
              text={<strong><i>Grade</i></strong>}
              predicate={[predicateNoExam, predicateExamNotFinalized, predicateSubmissionsEmpty, predicateNoGraderSelected]} />
            <TooltipLink
              to={'/overview/' + this.props.examID}
              text='Overview'
              predicate={[predicateNoExam, predicateExamNotFinalized, predicateSubmissionsEmpty]} />
            <TooltipLink
              to='/email'
              text='Email'
              predicate={[predicateNoExam, predicateExamNotFinalized, predicateSubmissionsEmpty]} />
            <ExportDropdown className='navbar-item' disabled={predicateSubmissionsEmpty[0]} examID={this.props.examID} />
            <a className='navbar-item' onClick={() => this.setHelpPage('shortcuts')}>
              {this.pages['shortcuts'].title}
            </a>
          </div>

          <div className='navbar-end'>
            {this.state.graderList.length
              ? <GraderDropdown grader={this.props.grader} list={this.state.graderList} changeGrader={this.props.changeGrader} />
              : <Link className='navbar-item' to='/graders'>Add grader</Link>
            }
            <div className='navbar-item'>
              <i>Version {__ZESJE_VERSION__}</i>
            </div>
          </div>
        </div>
        <HelpModal page={this.pages[this.state.helpPage] || {content: null, title: null}}
          closeHelp={() => this.setState({ helpPage: null })} />
      </nav>
    )
  }
}

export default NavBar
