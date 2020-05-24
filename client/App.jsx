import React from 'react'
import Loadable from 'react-loadable'
import { hot } from 'react-hot-loader'
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom'

import 'bulma/css/bulma.css'
import 'react-bulma-notification/build/css/index.css'
import 'font-awesome/css/font-awesome.css'

import * as api from './api.jsx'

import NavBar from './components/NavBar.jsx'
import Footer from './components/Footer.jsx'
import Loading from './views/Loading.jsx'

const Home = Loadable({
  loader: () => import('./views/Home.jsx'),
  loading: Loading
})
const AddExam = Loadable({
  loader: () => import('./views/AddExam.jsx'),
  loading: Loading
})
const Exam = Loadable({
  loader: () => import('./views/Exam.jsx'),
  loading: Loading
})
const Scans = Loadable({
  loader: () => import('./views/Scans.jsx'),
  loading: Loading
})
const Students = Loadable({
  loader: () => import('./views/Students.jsx'),
  loading: Loading
})
const Grade = Loadable({
  loader: () => import('./views/Grade.jsx'),
  loading: Loading
})
const Graders = Loadable({
  loader: () => import('./views/Graders.jsx'),
  loading: Loading
})
const Overview = Loadable({
  loader: () => import('./views/Overview.jsx'),
  loading: Loading
})
const Email = Loadable({
  loader: () => import('./views/Email.jsx'),
  loading: Loading
})
const Fail = Loadable({
  loader: () => import('./views/Fail.jsx'),
  loading: Loading
})

const nullExam = () => ({
  id: null,
  type: null,
  name: '',
  submissions: [],
  problems: [],
  widgets: [],
  finalized: false
})

class App extends React.Component {
  menu = React.createRef();

  state = {
    exam: nullExam(),
    grader: null
  }

  updateExam = (exam) => {
    this.setState({ exam: exam || nullExam() })
  }

  updateExamList = () => {
    if (this.menu.current) {
      this.menu.current.updateExamList()
    }
  }

  deleteExam = (examID) => {
    return api
      .del('exams/' + examID)
      .then(() => {
        this.updateExamList()
      })
  }

  changeGrader = (grader) => {
    this.setState({
      grader: grader
    })
    window.sessionStorage.setItem('graderID', grader.id)
  }

  render () {
    const exam = this.state.exam
    const grader = this.state.grader

    return (
      <Router>
        <div>
          <NavBar examID={exam.id} grader={grader} changeGrader={this.changeGrader} ref={this.menu} />
          <Switch>
            <Route exact path='/' component={Home} />
            <Route path='/exams/:examID' render={({ match, history }) =>
              <Exam
                examID={match.params.examID}
                updateExam={this.updateExam}
                updateExamList={this.updateExamList}
                deleteExam={this.deleteExam}
                leave={() => history.push('/')}
                setHelpPage={this.menu.current ? this.menu.current.setHelpPage : null} />} />
            <Route path='/exams' render={({ history }) =>
              <AddExam updateExamList={this.menu.current ? this.menu.current.updateExamList : null} changeURL={history.push} />} />
            <Route path='/scans/:examID' render={({ match }) =>
              <Scans examID={match.params.examID} />}
            />
            <Route path='/students/:examID' render={({ match }) =>
              <Students examID={match.params.examID} />}
            />
            <Route path='/grade' render={() => (
              exam.submissions.length && exam.problems.length && grader
                ? <Grade examID={exam.id} gradeAnonymous={exam.gradeAnonymous} graderID={this.state.grader.id} />
                : <Fail message='No exams uploaded or no grader selected. Please do not bookmark URLs' />
            )} />
            <Route path='/overview/:examID' render={({ match }) => (
              <Overview examID={match.params.examID} />
            )} />
            <Route path='/email' render={() => (
              exam.submissions.length ? <Email exam={exam} /> : <Fail message='No exams uploaded. Please do not bookmark URLs' />
            )} />
            <Route path='/graders' render={() =>
              <Graders updateGraderList={this.menu.current ? this.menu.current.updateGraderList : null} />} />
            <Route render={() =>
              <Fail message="404. Could not find that page :'(" />} />
          </Switch>
          <Footer />
        </div>
      </Router>
    )
  }
}

export default hot(module)(App)
