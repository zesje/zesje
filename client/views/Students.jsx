import React from 'react'
import Notification from 'react-bulma-notification'

import * as api from '../api.jsx'

import Hero from '../components/Hero.jsx'
import ProgressBar from '../components/ProgressBar.jsx'
import SearchBox from '../components/SearchBox.jsx'
import withShortcuts from '../components/ShortcutBinder.jsx'

import SearchPanel from './students/SearchPanel.jsx'
import EditPanel from './students/EditPanel.jsx'

import '../components/SubmissionNavigation.css'

class CheckStudents extends React.Component {
  state = {
    editActive: false,
    editStud: null,
    index: 0,
    copies: [],
    examID: null // The exam ID the loaded copies belong to
  }

  componentDidMount = () => {
    // If we change the keybindings here we should also remember to
    // update the tooltips for the associated widgets (in render()).
    // Also add the shortcut to ./client/components/help/ShortcutsHelp.md
    this.props.bindShortcut(['left', 'h'], this.prev)
    this.props.bindShortcut(['right', 'l'], this.next)
    this.props.bindShortcut(['up', 'k'], (event) => {
      event.preventDefault()
      this.nextUnchecked()
    })
    this.props.bindShortcut(['down', 'j'], (event) => {
      event.preventDefault()
      this.prevUnchecked()
    })

    this.fetchCopies()
  }

  componentDidUpdate = () => {
    if (this.state.examID !== this.props.examID) {
      this.fetchCopies()
    }
  }

  fetchCopies = () => {
    if (this.props.examID === null) return

    api.get(`copies/${this.props.examID}`).then(copies => {
      const newIndex = this.state.index < copies.length ? this.state.index : 0
      this.setState({
        index: newIndex,
        copies: copies,
        examID: this.props.examID
      })
    })
  }

  fetchCopy = (index) => {
    const copyNumber = this.state.copies[index].number
    api.get(`copies/${this.props.examID}/${copyNumber}`).then(copy => {
      let copies = [...this.state.copies]
      let oldIndex = copies.findIndex((copy) => copy.number === copyNumber)
      copies[oldIndex] = copy
      this.setState({ copies: copies })
    })
  }

  setCopyIndex = (newIndex) => {
    if (newIndex >= 0 && newIndex < this.state.copies.length) {
      this.setState({
        index: newIndex
      })
      this.fetchCopy(newIndex)
    }
  }

  prev = () => {
    this.setCopyIndex(this.state.index - 1)
  }
  next = () => {
    this.setCopyIndex(this.state.index + 1)
  }

  prevUnchecked = () => {
    for (let i = this.state.index - 1; i >= 0; i--) {
      if (this.state.copies[i].validated === false) {
        this.setCopyIndex(i)
        return
      }
    }
  }
  nextUnchecked = () => {
    for (let i = this.state.index + 1; i < this.state.copies.length; i++) {
      if (this.state.copies[i].validated === false) {
        this.setCopyIndex(i)
        return
      }
    }
  }

  matchStudent = (stud) => {
    if (!this.state.copies) return

    api.put(`copies/${this.props.examID}/${this.state.copies[this.state.index].number}`, { studentID: stud.id })
      .then(resp => {
        // TODO When do we want to update the full list of copies?
        this.fetchCopy(this.state.index)
        this.nextUnchecked()
      })
      .catch(err => {
        Notification.error('failed to put submission (see javascript console for details)')
        console.error('failed to put submission:', err)
        throw err
      })
  }

  toggleEdit = (student) => {
    if (student && student.id) {
      this.setState({
        editActive: true,
        editStud: student
      })
    } else {
      this.setState({
        editActive: !this.state.editActive,
        editStud: null
      })
      this.props.updateSubmission(this.props.exam.submissions[this.state.index].id)
    }
  }

  render () {
    const copies = this.state.copies
    const copy = copies[this.state.index]
    const validated = copy && copy.validated
    const total = copies.length
    const done = copies.filter(c => c.validated).length

    return (
      <div>

        <Hero title='Match Students' subtitle='Check that all submissions are correctly identified' />

        <section className='section'>

          <div className='container'>

            <div className='columns'>
              <div className='column is-one-quarter-desktop is-one-third-tablet'>
                {this.state.editActive
                  ? <EditPanel toggleEdit={this.toggleEdit} editStud={this.state.editStud} />
                  : <SearchPanel matchStudent={this.matchStudent} toggleEdit={this.toggleEdit} copy={copy}
                    student={copy && copy.student} validated={validated} copyIndex={this.state.index} />
                }
              </div>

              {this.state.copies.length
                ? <div className='column'>
                  <div className='level'>
                    <div className='level-item make-wider'>
                      <div className='field has-addons is-mobile'>
                        <div className='control'>
                          <button type='submit' className='button is-info is-rounded is-hidden-mobile'
                            onClick={this.prevUnchecked}>unchecked</button>
                          <button type='submit' className={'button' + (copy.validated ? ' is-success' : ' is-link')}
                            onClick={this.prev}>Previous</button>
                        </div>
                        <div className='control is-wider'>
                          <SearchBox
                            placeholder='Search for a copy'
                            selected={copy}
                            options={copies}
                            suggestionKeys={[
                              'number',
                              'student.firstName',
                              'student.lastName',
                              'student.id'
                            ]}
                            setSelected={this.setCopyIndex}
                            renderSelected={({number, student}) => {
                              if (student) {
                                return `#${number}: ${student.firstName} ${student.lastName} (${student.id})`
                              } else {
                                return `#${number}`
                              }
                            }}
                            renderSuggestion={(copy) => {
                              const stud = copy.student
                              if (stud) {
                                return (
                                  <div className='flex-parent'>
                                    <span className='flex-child truncated'>
                                      <b>#{copy.number}</b>
                                      {` ${stud.firstName} ${stud.lastName}`}
                                    </span>
                                    <i className='flex-child fixed'>
                                      ({stud.id})
                                    </i>
                                  </div>
                                )
                              } else {
                                return `#${copy.number}: No student`
                              }
                            }}
                          />
                        </div>
                        <div className='control'>
                          <button type='submit' className={'button' + (validated ? ' is-success' : ' is-link')}
                            onClick={this.next}>Next</button>
                          <button type='submit' className='button is-info is-rounded is-hidden-mobile'
                            onClick={this.nextUnchecked}>unchecked</button>
                        </div>
                      </div>
                    </div>
                  </div>

                  <ProgressBar done={done} total={total} />

                  <p className='box'>
                    <img src={'api/images/signature/' + this.state.examID + '/' + copy.number} alt='' />
                  </p>

                </div>
                : null}
            </div>
          </div>
        </section>

      </div>
    )
  }
}

export default withShortcuts(CheckStudents)
