import React from 'react'
import { Link } from 'react-router-dom'

import * as api from '../api.jsx'

const BurgerButton = (props) => (
  <button className={'button navbar-burger' + (props.foldOut ? ' is-active' : '')}
    onClick={props.burgerClick}>
    <span />
    <span />
    <span />
  </button>
)

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
    {label: 'Excel Spreadsheet', format: 'xlsx'},
    {label: 'Detailed Excel Spreadsheet', format: 'xlsx_detailed'},
    {label: 'Pandas Dataframe', format: 'dataframe'}
  ]

  const exportUrl = format => `/api/export/${format}/${props.exam.id}`

  return (
    <div className='navbar-item has-dropdown is-hoverable' style={props.style}>
      <div className='navbar-link'>
                Export
      </div>
      <div className='navbar-dropdown'>
        {exportFormats.map((exportFormat, i) =>
          <a className='navbar-item'
            href={exportUrl(exportFormat.format)}
            key={i}>
            {exportFormat.label}
          </a>
        )}
        <hr className='navbar-divider' />
        <a className='navbar-item' href='/api/export/full'>
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
      graderList: []
    }

    componentDidMount = () => {
      this.updateExamList()
      this.updateGraderList()
    }

    updateExamList = () => {
      api.get('exams')
        .then(exams => {
          this.setState({
            examList: exams
          })
          if (this.props.exam.id == null && exams.length) this.props.updateExam(exams[exams.length - 1].id)
        })
    }

    updateGraderList = () => {
      api.get('graders')
        .then(graders => {
          this.setState({
            graderList: graders
          })
        })
    }

    burgerClick = () => {
      this.setState({
        foldOut: !this.state.foldOut
      })
    }

    render () {
      const examStyle = this.props.exam.submissions.length && this.props.grader ? {} : { pointerEvents: 'none', opacity: 0.65 }
      const statsStyle = this.props.exam.submissions.length ? {} : { pointerEvents: 'none', opacity: 0.65 }

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

              <Link className='navbar-item' to={'/submissions/' + this.props.exam.id}>Submissions</Link>
              <Link className='navbar-item' to='/students'>Students</Link>
              <Link className='navbar-item' style={examStyle} to='/grade'><strong><i>Grade</i></strong></Link>
              <Link className='navbar-item' style={statsStyle} to='/statistics'>Statistics</Link>
              <ExportDropdown className='navbar-item' style={examStyle} exam={this.props.exam} />
            </div>

            <div className='navbar-end'>
              {this.state.graderList.length
                ? <GraderDropdown grader={this.props.grader} list={this.state.graderList} changeGrader={this.props.changeGrader} />
                : <Link className='navbar-item' to='/graders'>Add grader</Link>
              }
              <Link className='navbar-item has-text-info' to='/reset'>reset</Link>
              <div className='navbar-item'>
                <i>Version {__COMMIT_HASH__}</i>
              </div>
            </div>
          </div>
        </nav>
      )
    }
}

export default NavBar
