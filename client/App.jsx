import React from 'react'
import Loadable from 'react-loadable'
import { hot } from 'react-hot-loader'
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom'

import 'bulma/css/bulma.css'
import 'react-bulma-notification/build/css/index.css'
import 'font-awesome/css/font-awesome.css'

import NavBar from './components/NavBar.jsx'
import ExamRouter from './components/ExamRouter.jsx'
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
const Graders = Loadable({
  loader: () => import('./views/Graders.jsx'),
  loading: Loading
})

const Fail = Loadable({
  loader: () => import('./views/Fail.jsx'),
  loading: Loading
})

class App extends React.Component {
  menu = React.createRef();

  state = {
    examID: null,
    grader: null
  }

  selectExam = (id) => {
    this.setState({ examID: parseInt(id) })
  }

  updateExamList = () => {
    if (this.menu.current) {
      this.menu.current.updateExamList()
    }
  }

  changeGrader = (grader) => {
    this.setState({
      grader: grader
    })
    window.sessionStorage.setItem('graderID', grader.id)
  }

  render () {
    const grader = this.state.grader
    const updateExamList = this.menu.current ? this.menu.current.updateExamList : () => {}
    const updateGraderList = this.menu.current ? this.menu.current.updateGraderList : () => {}
    const setHelpPage = this.menu.current ? this.menu.current.setHelpPage : (help) => {}

    return (
      <Router>
        <div>
          <NavBar examID={this.state.examID} grader={grader} changeGrader={this.changeGrader} ref={this.menu} />
          <Switch>
            <Route exact path='/' component={Home} />
            <Route exact path='/exams' render={({ history }) =>
              <AddExam updateExamList={updateExamList} changeURL={history.push} />}
            />
            <Route path='/exams/:examID/' render={({ match }) =>
              <ExamRouter
                parentURL={match.url}
                examID={match.params.examID}
                graderID={grader ? grader.id : null}
                selectExam={this.selectExam}
                updateExamList={updateExamList}
                setHelpPage={setHelpPage} />
            } />
            <Route exact path='/graders' render={() =>
              <Graders updateGraderList={updateGraderList} />} />
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
