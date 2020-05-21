import React from 'react'
import {Link} from 'react-router-dom'

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

const ExamDropdown = (props) => (
  <div className='navbar-item has-dropdown is-hoverable'>
    <Link className='navbar-link' to={'/exams/' + (props.exam.id ? props.exam.id : '')}>
      {props.exam.id ? <i>{props.exam.name}</i> : 'Add exam'}
    </Link>
    <div className='navbar-dropdown'>
      {props.list.map((exam) => (
        <Link className={'navbar-item' + (props.exam.id === exam.id ? ' is-active' : '')}
          to={'/exams/' + exam.id} key={exam.id} >
          <i>{exam.name}</i>
        </Link>
      ))}
      <hr className='navbar-divider' />
      <Link className='navbar-item' to={'/exams'} >
        Add new
      </Link>
    </div>
  </div>
)

const GraderDropdown = (props) => {
  if (props.hidden) { return null } else {
    return (
      <div className='navbar-item has-dropdown is-hoverable'>
        <div className='navbar-link' >
          <i>{props.grader}</i>
        </div>

        <div className='navbar-dropdown'>
          <Link className='navbar-item' to={'/graders'} >
        Add grader
          </Link>
        </div>
      </div>
    )
  }
}

const ExportDropdown = (props) => {
  const exportFormats = [
    { label: 'Excel Spreadsheet', format: 'xlsx' },
    { label: 'Detailed Excel Spreadsheet', format: 'xlsx_detailed' },
    { label: 'Pandas Dataframe', format: 'dataframe' },
    { label: 'Zip of (anonymized) pdf files', format: 'pdf' }
  ]

  const exportUrl = format => `/api/export/${format}/${props.exam.id}`

  return (
    <div className='navbar-item has-dropdown is-hoverable'>
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
          href={'/api/export/graders/' + props.exam.id}
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

const LoginButton = (props) => {
  if (props.hidden) { return null } else {
    return (<Link className='navbar-item' hidden onClick={props.logout} to='/login'>Logout</Link>)
  }
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
    grader: ''
  }

  componentDidMount = () => {
    this.updateGrader()
  }

  updateExamList = () => {
    api.get('exams')
      .then(exams => {
        this.setState({
          examList: exams
        })
        const examIDs = exams.map(exam => exam.id)
        const examID = this.props.exam.id
        if (!examIDs.includes(examID) || examID === null) {
          if (!exams.length) {
            this.props.updateExam(null)
          } else {
            this.props.updateExam(exams[exams.length - 1].id)
          }
        }
      })
  }
  updateGrader = () => {
    if (window.location.pathname !== '/login') {
      api.get('oauth/grader').then(response => {
        this.setState({grader: response})
        this.props.changeGrader(response)
        this.updateExamList()
      })
    }
  }

  burgerClick = () => {
    this.setState({
      foldOut: !this.state.foldOut
    })
  }

  setHelpPage = (helpPage) => {
    this.setState({ helpPage: helpPage })
  }

  logout = () => {
    this.setState({grader: ''})
    api.get('oauth/logout')
      .catch(response => { console.log(response) })
  }

  displayGrader = () => {
    if (this.state.grader) {
      return 'Current Grader: ' + this.state.grader.name + ' (' + this.state.grader.oauth_id + ')'
    } else {
      return ''
    }
  }

  render () {
    const predicateExamNotFinalized = [!this.props.exam.finalized, 'The exam is not finalized yet.']
    const predicateSubmissionsEmpty = [this.props.exam.submissions.length === 0, 'There are no submissions, please upload some.']
    const predicateNoGraderSelected = [this.props.grader === null, 'Please select a grader.']

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
              ? <ExamDropdown exam={this.props.exam} list={this.state.examList} />
              : <Link className='navbar-item' to='/exams'>Add exam</Link>
            }

            <TooltipLink
              to={'/scans/' + this.props.exam.id}
              text='Scans'
              predicate={[predicateExamNotFinalized]} />
            <Link className='navbar-item' to={'/students/' + this.props.exam.id}>Students</Link>
            <TooltipLink
              to='/grade'
              text={<strong><i>Grade</i></strong>}
              predicate={[predicateExamNotFinalized, predicateSubmissionsEmpty, predicateNoGraderSelected]} />
            <TooltipLink
              to={'/overview/' + this.props.exam.id}
              text='Overview'
              predicate={[predicateExamNotFinalized, predicateSubmissionsEmpty]} />
            <TooltipLink
              to='/email'
              text='Email'
              predicate={[predicateExamNotFinalized, predicateSubmissionsEmpty]} />
            <ExportDropdown className='navbar-item' disabled={predicateSubmissionsEmpty[0]} exam={this.props.exam} />
            <a className='navbar-item' onClick={() => this.setHelpPage('shortcuts')}>
              {this.pages['shortcuts'].title}
            </a>
          </div>

          <div className='navbar-end'>
            <GraderDropdown grader={this.displayGrader()} hidden={!`this.state.grader`} />
            <LoginButton className='navbar-item' hidden={!this.state.grader} logout={this.logout} />

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
