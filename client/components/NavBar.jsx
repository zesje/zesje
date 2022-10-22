import React from 'react'
import { Link } from 'react-router-dom'

import './NavBar.scss'
import * as api from '../api.jsx'

const BurgerButton = (props) => (
  <button
    className={'button navbar-burger is-info' + (props.foldOut ? ' is-active' : '')}
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
    <a
      className={'navbar-item' + (pred[0] ? ' tooltip has-tooltip-bottom' : '')}
      data-tooltip={pred[1]}
    >
      <Link
        className={'navbar-item'}
        disabled={pred[0]}
        to={props.to}>
        {props.text}
      </Link>
    </a>
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
            className='navbar-item'
            to={'/exams/' + exam.id} key={exam.id}
          >
            <i className={(props.selectedExam && props.selectedExam.id === exam.id ? 'has-text-info' : '')}>
              {exam.name}
            </i>
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
  return (
    <div className='navbar-item has-dropdown is-hoverable'>
      <div className='navbar-link'>
        <span className='icon'>
          <i className='fa fa-user-circle' aria-hidden='true' />
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
        >
          Export full database
        </a>
      </div>
    </div>
  )
}

class NavBar extends React.Component {
  state = {
    foldOut: false,
    examList: [],
    examID: null,
    loginProvider: ''
  }

  componentDidMount = () => this.updateExamList()

  componentDidUpdate = (prevProps, prevState) => {
    if (prevProps.examID !== this.props.examID && !isNaN(this.props.examID)) {
      this.setState({ examID: this.props.examID })
    }
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

  render () {
    const selectedExam = this.state.examList.find(exam => exam.id === this.state.examID)

    const predicateNoExam = [!selectedExam, 'No exam selected.']
    const predicateExamNotFinalized = [predicateNoExam[0] || !selectedExam.finalized,
      'The exam is not finalized yet.']
    const predicateSubmissionsEmpty = [predicateNoExam[0] || selectedExam.submissions.length === 0,
      'There are no submissions, please upload some.']

    return (
      <nav className='navbar is-info has-shadow' role='navigation' aria-label='dropdown navigation'>

        <div className='navbar-brand'>
          <div className='navbar-item'>
            <span className='icon is-medium'>
              <i className='fa fa-edit fa-2x' />
            </span>
          </div>

          <Link className='navbar-item' to='/'><b>Zesje</b></Link>
          <div className='navbar-item' />

          <BurgerButton foldOut={this.props.foldOut} burgerClick={this.burgerClick} />
        </div>

        <div className={'navbar-menu' + (this.state.foldOut ? ' is-active' : '')} onClick={this.burgerClick}>
          <div className='navbar-start'>

            {this.state.examList.length
              ? <ExamDropdown selectedExam={selectedExam} list={this.state.examList} />
              : <TooltipLink to='/exams' text='Add exam' predicate={[]} />}

            <TooltipLink
              to={`/exams/${this.state.examID}/scans`}
              text='Scans'
              predicate={[predicateExamNotFinalized]}
            />
            <TooltipLink
              to={`/exams/${this.state.examID}/students`}
              text='Students'
              predicate={[predicateNoExam]}
            />
            <TooltipLink
              to={`/exams/${this.state.examID}/grade`}
              text={<strong><i>Grade</i></strong>}
              predicate={[predicateNoExam, predicateExamNotFinalized, predicateSubmissionsEmpty]}
            />
            <TooltipLink
              to={`/exams/${this.state.examID}/overview`}
              text='Overview'
              predicate={[predicateNoExam, predicateExamNotFinalized, predicateSubmissionsEmpty]}
            />
            <TooltipLink
              to={`/exams/${this.state.examID}/email`}
              text='Email'
              predicate={[predicateExamNotFinalized, predicateSubmissionsEmpty]}
            />
            <ExportDropdown
              disabled={predicateNoExam[0] || predicateSubmissionsEmpty[0]}
              examID={this.state.examID}
            />
            <a className='navbar-item' onClick={() => this.props.setHelpPage('shortcuts')}>
              Shortcuts
            </a>
          </div>

          <div className='navbar-end'>
            <GraderDropdown
              grader={this.props.grader}
              logout={this.props.logout} />
          </div>

        </div>
      </nav>
    )
  }
}

export default NavBar
