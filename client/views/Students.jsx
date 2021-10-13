import React from 'react'
import ReactDOMServer from 'react-dom/server'
import { toast } from 'bulma-toast'

import * as api from '../api.jsx'

import Hero from '../components/Hero.jsx'
import ProgressBar from '../components/ProgressBar.jsx'
import SearchBox from '../components/SearchBox.jsx'
import withShortcuts from '../components/ShortcutBinder.jsx'
import ConfirmationModal from '../components/ConfirmationModal.jsx'
import Fail from './Fail.jsx'

import SearchPanel from './students/SearchPanel.jsx'
import EditPanel from './students/EditPanel.jsx'

import '../components/SubmissionNavigation.css'

const ConfirmMergeModal = (props) => {
  if (!props.student) return null

  let msg = ''
  const other = props.copies.filter(c => c.student.id === props.student.id)

  msg = <p>
    Student #{props.student.id} is already matched with {other.length > 1 ? 'copies' : 'copy'}&nbsp;
    {other.reduce((prev, c, index) =>
      prev + `${c.number}${index < other.length - 2 ? ', ' : (index === other.length - 1 ? '' : ' and ')}`, '')}.
    &nbsp;This action will merge {other.length > 1 ? 'them' : 'it'}
    &nbsp;with this copy which might affect the total score of the problem.
    &nbsp;Moreover, the solution will have to be approved again.
    <br/>
    Note that this action <b>cannot be undone</b>.
  </p>

  return <ConfirmationModal
    headerText={'Are you sure you want to merge these copies?'}
    contentText={msg}
    color='is-danger'
    confirmText='Merge copies'
    active
    onConfirm={props.onConfirm}
    onCancel={props.onCancel}
  />
}

class CheckStudents extends React.Component {
  state = {
    editActive: false,
    editStud: null,
    confirmStudent: null,
    index: 0,
    copies: [],
    examID: undefined // The exam ID the loaded copies belong to
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

  componentDidUpdate = (prevProps, prevState) => {
    if (prevProps.examID !== this.props.examID) {
      this.fetchCopies()
    }
  }

  fetchCopies = () => {
    if (!this.props.examID || isNaN(this.props.examID)) return

    api.get(`copies/${this.props.examID}`).then(copies => {
      const newIndex = this.state.index < copies.length ? this.state.index : 0
      this.setState({
        index: newIndex,
        copies: copies,
        examID: this.props.examID
      })
    }).catch(err => {
      console.log(err)
      this.setState({
        index: 0,
        copies: [],
        examID: null
      })
    })
  }

  fetchCopy = (index) => {
    const copyNumber = this.state.copies[index].number
    api.get(`copies/${this.props.examID}/${copyNumber}`).then(copy => {
      const copies = [...this.state.copies]
      const oldIndex = copies.findIndex((copy) => copy.number === copyNumber)
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

  selectCopy = (copy) => {
    this.setCopyIndex(this.state.copies.findIndex((c) => c.number === copy.number))
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

  matchStudent = (stud, force = false) => {
    if (!this.state.copies) return

    const hasOtherCopies = this.state.copies.filter(c => c.student.id === stud.id).length > 0
    if (hasOtherCopies && !force) {
      this.setState({ confirmStudent: stud })
    } else {
      api.put(`copies/${this.props.examID}/${this.state.copies[this.state.index].number}`, { studentID: stud.id })
        .then(resp => {
          // TODO When do we want to update the full list of copies?
          if (this.state.confirmStudent !== null) this.setState({ confirmStudent: null })
          this.fetchCopy(this.state.index)
          this.nextUnchecked()

          const msg = <p>Student matched with copy {this.state.copies[this.state.index].number}, go to&nbsp;
            <a href={`/exams/${this.state.examID}/grade/${resp.new_submission_id}`}>Grade</a>&nbsp;
            to approve the merged submission.</p>

          toast({
            message: ReactDOMServer.renderToString(msg),
            type: 'is-success',
            pauseOnHover: true,
            duration: 5000
          })
        })
        .catch(err => {
          err.json().then(res => {
            toast({ message: `Failed to validate copy: ${res.message}`, type: 'is-danger' })
          })
        })
    }
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
    }
  }

  render () {
    const copies = this.state.copies
    const copy = copies[this.state.index]
    const validated = copy && copy.validated
    const total = copies.length
    const done = copies.filter(c => c.validated).length

    const hero = <Hero title='Match Students' subtitle='Check that all submissions are correctly identified' />

    if (this.state.examID === undefined && this) return hero

    if (!this.state.examID) {
      return <Fail message='No copies where found for this exam' />
    }

    return (
      <div>

        {hero}

        <section className='section'>

          <div className='container'>

            <div className='columns'>
              <div className='column is-one-quarter-desktop is-one-third-tablet'>
                {this.state.editActive
                  ? <EditPanel toggleEdit={this.toggleEdit} editStud={this.state.editStud} />
                  : <SearchPanel
                    matchStudent={this.matchStudent} toggleEdit={this.toggleEdit} copy={copy}
                    student={copy && copy.student} validated={validated} copyIndex={this.state.index}
                    />}
              </div>

              {this.state.copies.length
                ? <div className='column'>
                  <div className='level'>
                    <div className='level-item make-wider'>
                      <div className='field has-addons is-mobile'>
                        <div className='control'>
                          <button
                            type='submit' className='button is-info is-rounded is-hidden-mobile'
                            onClick={this.prevUnchecked}
                          >unchecked
                          </button>
                          <button
                            type='submit'
                            className={'button is-radiusless' + (copy.validated ? ' is-success' : ' is-link')}
                            onClick={this.prev}
                          >Previous
                          </button>
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
                            setSelected={this.selectCopy}
                            renderSelected={({ number, student }) => {
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
                          <button
                            type='submit' className={'button is-radiusless' + (validated ? ' is-success' : ' is-link')}
                            onClick={this.next}
                          >Next
                          </button>
                          <button
                            type='submit' className='button is-info is-rounded is-hidden-mobile'
                            onClick={this.nextUnchecked}
                          >unchecked
                          </button>
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

            <ConfirmMergeModal
              student={this.state.confirmStudent}
              copies={this.state.copies}
              onConfirm={() => this.matchStudent(this.state.confirmStudent, true)}
              onCancel={() => { this.setState({ confirmStudent: null }) }}
            />
          </div>
        </section>

      </div>
    )
  }
}

export default withShortcuts(CheckStudents)
