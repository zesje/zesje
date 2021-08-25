import React from 'react'
import { Link } from 'react-router-dom'

import './NavBar.css'
import * as api from '../api.jsx'

import HelpModal from './help/HelpModal.jsx'
import shortcutsMarkdown from './help/ShortcutsHelp.md'
import gradingPolicyMarkdown from './help/GradingPolicyHelp.md'
import Login from './Login.jsx'

const BurgerButton = (props) => (
  <button
    className={'button navbar-burger' + (props.foldOut ? ' is-active' : '')}
    onClick={props.burgerClick}
  >
    <span />
    <span />
    <span />
  </button>
)

const TooltipLink = (props) => {
  let pred = props.predicate.find(pred => pred[0])
  if (!pred) pred = [false, null]

  return (
    <div
      className={'navbar-item no-padding' + (pred[0] ? ' tooltip has-tooltip-bottom' : '')}
      data-tooltip={pred[1]}
    >
      <Link className='navbar-item' disabled={pred[0]} to={props.to}> {props.text} </Link>
    </div>
  )
}

const ExamDropdown = (props) => {
  return (
    <div className='navbar-item has-dropdown is-hoverable'>
      <Link className='navbar-link' to={'/exams/' + (props.selectedExam ? props.selectedExam.id : '')}>
        {props.selectedExam ? <i>{props.selectedExam.name}</i> : 'Add exam'}
      </Link>
      <div className='navbar-dropdown'>
        {props.list.map((exam) => (
          <Link
            className={'navbar-item' + (props.selectedExam && props.selectedExam.id === exam.id ? ' is-active' : '')}
            to={'/exams/' + exam.id} key={exam.id}
          >
            <i>{exam.name}</i>
          </Link>
        ))}
        <hr className='navbar-divider' />
        <Link className='navbar-item' to='/exams'>
          Add new
        </Link>
      </div>
    </div>
  )
}

const GraderDropdown = (props) => {
  if (!props.grader) {
    return (
      <div className='navbar-item'>
        <Login />
      </div>
    )
  }

  return (
    <div className='navbar-item has-dropdown is-hoverable'>
      <div className='navbar-link'>
        <span className='icon'>
          <i className='fa fa-user-circle-o' aria-hidden='true' />
        </span>
        <span>
          {props.grader.name} ({props.grader.oauth_id})
        </span>
      </div>

      <div className='navbar-dropdown'>
        <Link className='navbar-item' to='/graders'>
          Add grader
        </Link>
        <hr className='navbar-divider' />
        <Link className='navbar-item' onClick={props.logout} to='/'>Logout</Link>
      </div>
    </div>
  )
}

const ExportDropdown = (props) => {
  const exportFormats = [
    { label: 'Excel Spreadsheet', format: 'xlsx' },
    { label: 'Detailed Excel Spreadsheet', format: 'xlsx_detailed' },
    { label: 'Pandas Dataframe', format: 'dataframe' },
    { label: 'Zip of (anonymized) pdf files', format: 'pdf' }
  ]

  const exportUrl = format => `/api/export/${format}/${props.examID}`

  return (
    <div className='navbar-item has-dropdown is-hoverable'>
      <div className='navbar-link'>
        Export
      </div>
      <div className='navbar-dropdown'>
        {exportFormats.map((exportFormat, i) =>
          <a
            className='navbar-item'
            href={exportUrl(exportFormat.format)}
            disabled={props.disabled}
            key={i}
          >
            {exportFormat.label}
          </a>
        )}
        <hr className='navbar-divider' />
        <a
          className='navbar-item'
          href={'/api/export/graders/' + props.examID}
          disabled={props.disabled}
        >
          Export grader statistics
        </a>
        <hr className='navbar-divider' />
        <a
          className='navbar-item'
          href='/api/export/full'
          disabled={props.fullDisabled}
        >
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
    grader: null,
    helpPage: null,
    examID: null
  }

  componentDidUpdate = (prevProps, prevState) => {
    if (prevProps.examID !== this.props.examID && !isNaN(this.props.examID)) {
      this.setState({ examID: this.props.examID })
    }
  }

  componentDidMount = () => {
    this.updateGrader()
  }

  updateExamList = () => {
    api.get('exams')
      .then(exams => {
        let exam = exams.find(exam => exam.id === this.state.examID)
        if (!exam && exams.length) exam = exams[exams.length - 1]

        this.setState(prevState => ({
          examList: exams,
          examID: exam ? exam.id : null
        }))
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

  updateGrader = () =>
    api.get('oauth/grader').then(grader => {
      console.log(grader)
      this.setState({ grader })
      this.props.setGrader(grader)
      this.updateExamList()
    })

  logout = () =>
    api.get('oauth/logout')
      .then(() => {
        this.setState({
          grader: null,
          examList: [],
          examID: null
        })
        this.props.setGrader(null)
      })

  render () {
    const selectedExam = this.state.examList.find(exam => exam.id === this.state.examID)

    const predicateNoGrader = [!this.state.grader, 'Log in before using the app.']
    const predicateNoExam = [!selectedExam, 'No exam selected.']
    const predicateExamNotFinalized = [predicateNoExam[0] || !selectedExam.finalized,
      'The exam is not finalized yet.']
    const predicateSubmissionsEmpty = [predicateNoExam[0] || selectedExam.submissions.length === 0,
      'There are no submissions, please upload some.']

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

            {this.state.examList.length && this.state.grader
              ? <ExamDropdown selectedExam={selectedExam} list={this.state.examList} />
              : <TooltipLink to='/exams' text='Add exam' predicate={[predicateNoGrader]} />}

            <TooltipLink
              to={`/exams/${this.state.examID}/scans`}
              text='Scans'
              predicate={[predicateNoGrader, predicateExamNotFinalized]}
            />
            <TooltipLink
              to={`/exams/${this.state.examID}/students`}
              text='Students'
              predicate={[predicateNoGrader, predicateNoExam]}
            />
            <TooltipLink
              to={`/exams/${this.state.examID}/grade`}
              text={<strong><i>Grade</i></strong>}
              predicate={[predicateNoGrader, predicateNoExam, predicateExamNotFinalized, predicateSubmissionsEmpty]}
            />
            <TooltipLink
              to={`/exams/${this.state.examID}/overview`}
              text='Overview'
              predicate={[predicateNoGrader, predicateNoExam, predicateExamNotFinalized, predicateSubmissionsEmpty]}
            />
            <TooltipLink
              to={`/exams/${this.state.examID}/email`}
              text='Email'
              predicate={[predicateNoGrader, predicateExamNotFinalized, predicateSubmissionsEmpty]}
            />
            <ExportDropdown
              disabled={predicateNoExam[0] || predicateSubmissionsEmpty[0]}
              fullDisabled={predicateNoGrader[0]}
              examID={this.state.examID}
            />
            <a className='navbar-item' onClick={() => this.setHelpPage('shortcuts')}>
              {this.pages.shortcuts.title}
            </a>
          </div>

          <div className='navbar-end'>
            <GraderDropdown grader={this.state.grader} logout={this.logout} />
          </div>

        </div>
        <HelpModal
          page={this.pages[this.state.helpPage] || { content: null, title: null }}
          closeHelp={() => this.setState({ helpPage: null })}
        />
      </nav>
    )
  }
}

export default NavBar
