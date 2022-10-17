import React from 'react'
import loadable from '@loadable/component'
import { hot } from 'react-hot-loader'
import { BrowserRouter as Router, Route, Routes, Navigate, Outlet, useLocation } from 'react-router-dom'

import './App.scss'

import * as api from './api.jsx'

import NavBar from './components/NavBar.jsx'
import ExamRouter from './components/ExamRouter.jsx'
import Footer from './components/Footer.jsx'
import Loading from './views/Loading.jsx'
import HelpModal, { HELP_PAGES } from './components/modals/HelpModal.jsx'

const Login = loadable(() => import('./views/Login.jsx'), { fallback: <Loading /> })
const Home = loadable(() => import('./views/Home.jsx'), { fallback: <Loading /> })
const AddExam = loadable(() => import('./views/AddExam.jsx'), { fallback: <Loading /> })
const Graders = loadable(() => import('./views/Graders.jsx'), { fallback: <Loading /> })
const Fail = loadable(() => import('./views/Fail.jsx'), { fallback: <Loading /> })

const NavBarView = (props) => {
  const location = useLocation()

  return props.grader == null
    ? <Navigate to={{ pathname: '/login', search: `from=${location.pathname}` }} state={{ from: location }} replace />
    : <div>
      <NavBar
        logout={props.logout}
        ref={props.menu}
        grader={props.grader}
        examID={props.examID}
        setHelpPage={props.setHelpPage} />
      <section className='section'>
        <div className='container is-fluid'>
          <Outlet />
        </div>
      </section>
      <HelpModal
        page={HELP_PAGES[props.helpPage] || { content: null, title: null }}
        closeHelp={() => props.setHelpPage({ helpPage: null })}
      />
      <Footer />
    </div>
}

class App extends React.Component {
  state = {
    examID: null,
    /*
    * The id of the current user. An undefined user means that the App has not check the backend for the registrered
    * user yet, hence wait for the response before going to the desired url by showing a Home/Welcome screen.
    * Instead, a null user means that is not logged in, then go to the Home page through the router.
    */
    grader: undefined,
    helpPage: null
  }

  constructor (props) {
    super(props)
    this.menu = React.createRef()
  }

  componentDidMount = () => {
    api.get('oauth/status').then(status => {
      this.setState({
        grader: status.grader,
        loginProvider: status.provider
      })
    }).catch(err => {
      if (err.status === 401) {
        err.json().then(status => {
          this.setState({
            grader: null,
            loginProvider: status.provider
          })
        })
      } else {
        console.log(err)
      }
    })
  }

  selectExam = (id) => this.setState({ examID: parseInt(id) })
  logout = () => api.get('oauth/logout').then(() => this.setState({ grader: null }))
  setHelpPage = (helpPage) => this.setState({ helpPage: helpPage })

  updateExamList = () => {
    if (this.menu.current) {
      this.menu.current.updateExamList()
    }
  }

  render () {
    if (this.state.grader === undefined) return <Loading />

    return (
      <Router>
        <Routes>
          <Route path='login' element={
            <Login provider={this.state.loginProvider} grader={this.state.grader} />
          } />
          <Route path='unauthorized' element={
              <Fail message='Your account is not authorized to access this instance of Zesje.' />
          }/>
          <Route path='*' element={<Fail message="404. Could not find that page :'(" />}/>
          <Route path='/' element={
            <NavBarView
              logout={this.logout}
              menu={this.menu}
              grader={this.state.grader}
              examID={this.state.examID}
              setHelpPage={this.setHelpPage}
              helpPage={this.state.helpPage} />
          }>
            <Route index element={<Home />} />
            <Route path='exams' element={<Outlet />}>
              <Route index element={<AddExam updateExamList={this.updateExamList}/>} />
              <Route path=':examID/*' element={
                <ExamRouter
                  selectExam={this.selectExam}
                  updateExamList={this.updateExamList}
                  setHelpPage={this.setHelpPage}
                />}
              />
            </Route>
            <Route path='graders' element={<Graders />} />
          </Route>
        </Routes>
      </Router>
    )
  }
}

export default hot(module)(App)
