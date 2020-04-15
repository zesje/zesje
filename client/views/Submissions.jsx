import React from 'react'

import Notification from 'react-bulma-notification'
import Dropzone from 'react-dropzone'

import Hero from '../components/Hero.jsx'
import DropzoneContent from '../components/DropzoneContent.jsx'

import * as api from '../api.jsx'

const ScanStatus = (props) => {
  let iconClass = 'fa fa-'
  switch (props.scan.status) {
    case 'processing':
      iconClass += 'refresh fa-spin'
      break
    case 'success':
      iconClass += 'check'
      break
    case 'error':
      iconClass += 'times'
      break
  }
  const messageParts = props.scan.message ? props.scan.message.split('\n') : ['']
  const summary = messageParts[0]
  const hasDetails = messageParts.length > 1
  return (
    <div>
      {props.scan.name}&emsp;<i className={iconClass} />
      <i>&nbsp;{summary}</i>
      {hasDetails
        ? <details>
          <summary>View details</summary>
          {messageParts.slice(1).map((msg, index) =>
            <li key={index}>
              {msg}
            </li>
          )}
        </details>
        : null
      }
    </div>
  )
}

class Submissions extends React.Component {
  state = {
    scans: [],
    submissions: [],
    examID: null,
    showOtherUploadOptions: false
  };

  updateScans = () => {
    api.get('scans/' + this.props.exam.id)
      .then(scans => {
        if (JSON.stringify(scans) !== JSON.stringify(this.state.scans)) {
          this.setState({
            scans: scans
          })
          this.updateSubmissions()
        }
      })
  }

  updateSubmissions = () => {
    api.get('submissions/missing_pages/' + this.props.exam.id)
      .then(submissions => {
        this.setState({
          submissions: submissions.map(sub => ({
            id: sub['id'],
            missing: sub['missing_pages']
          }))
        })
      })
  }

  onDropPDF = (accepted, rejected) => {
    if (rejected.length > 0) {
      Notification.error('Please upload a scan PDF.')
      return
    }
    accepted.map(file => {
      const data = new window.FormData()
      data.append('pdf', file)
      api.post('scans/' + this.props.exam.id, data)
        .then(() => {
          this.updateScans()
        })
        .catch(resp => {
          Notification.error('failed to upload pdf (see javascript console for details)')
          console.error('failed to upload PDF:', resp)
        })
    })
  }

  onDropZIP = (accepted, rejected) => {
    if (rejected.length > 0) {
      Notification.error('Please upload a ZIP file.')
      return
    }
    accepted.map(file => {
      const data = new window.FormData()
      data.append('file', file)
      api.post('scans/raw/' + this.props.exam.id, data)
        .then(() => {
          this.updateScans()
        })
        .catch(resp => {
          Notification.error('failed to upload ZIP (see javascript console for details)')
          console.error('failed to upload ZIP:', resp)
        })
    })
  }

  componentDidMount = () => {
    this.scanUpdater = setInterval(this.updateScans, 1000)
    this.updateScans()
    // TODO: remove this when https://gitlab.kwant-project.org/zesje/zesje/issues/173
    //       has been solved. This is a
    api.get('students')
      .then(students => {
        if (students.length === 0) {
          Notification.info(
            'You have not yet uploaded any students. ' +
            "If you don't upload students before the scans " +
            "then we can't automatically assign students " +
            'to their submissions',
            { 'duration': 5 }
          )
        }
      })
  }

  componentWillUnmount = () => {
    clearInterval(this.scanUpdater)
  }

  render () {
    const missingSubmissions = this.state.submissions.filter(s => s.missing.length > 0)

    const missingSubmissionsStatus = (
      missingSubmissions.length > 0
        ? <div>
          <p className='menu-label'>
            Missing Pages
          </p>
          <ul className='menu-list'>
            {missingSubmissions.map(sub =>
              <li key={sub.id}>
                Copy {sub.id} is missing pages {sub.missing.join(',')}
              </li>
            )}
          </ul>
        </div>
        : null
    )

    return <div>

      <Hero title='Exam details' subtitle={'Selected: ' + this.props.exam.name} />

      <section className='section'>

        <div className='container'>
          <div className='columns is-centered is-multiline'>
            <div className='column has-text-centered is-full'>
              <h3 className='title'>Upload scans</h3>
              <Dropzone accept={'application/pdf'} style={{}}
                activeStyle={{ borderStyle: 'dashed', width: 'fit-content', margin: 'auto' }}
                onDrop={this.onDropPDF}
                disablePreview
                multiple>
                <DropzoneContent text='Choose a PDF file…' />
              </Dropzone>
            </div>
            <div className='column is-half'>
              <div className='card'>
                <header className='card-header'
                  onClick={() => this.setState({showOtherUploadOptions: !this.state.showOtherUploadOptions})}>
                  <a className='a card-header-icon'>
                    <span className='icon'>
                      <i className={'fa fa-angle-' + (this.state.showOtherUploadOptions ? 'up' : 'down')}
                        aria-hidden='true' />
                    </span>
                  </a>
                  <a className='card-header-title'>
                    Other upload options
                  </a>
                </header>
                <div className='card-content'
                  hidden={!this.state.showOtherUploadOptions}>
                  <div className='content'>
                    It is also possible to upload pictures of pages made by students.
                    These should be contained in a ZIP file, for the exact format and
                    more information please refer to <a href='/#image-based-exam'>Home#image-based-exam</a>.
                  </div>
                  <Dropzone
                    accept={'application/zip,application/octet-stream,application/x-zip-compressed,multipart/x-zip'}
                    style={{}}
                    activeStyle={{ borderStyle: 'dashed', width: 'fit-content', margin: 'auto' }}
                    onDrop={this.onDropZIP}
                    disablePreview
                    multiple>
                    <DropzoneContent text='Choose a ZIP file…' />
                  </Dropzone>
                </div>
              </div>
            </div>
            <div className='column is-full has-text-centered'>
              <aside className='menu'>
                <p className='menu-label'>
                  Uploaded submissions: {this.state.submissions.length}
                </p>

                {missingSubmissionsStatus}

                <p className='menu-label'>
                  Upload History
                </p>
                <ul className='menu-list'>
                  {this.state.scans.map(scan =>
                    <li key={scan.id}>
                      <ScanStatus scan={scan} />
                    </li>
                  )}
                </ul>
              </aside>
            </div>
          </div>
        </div>
      </section>
    </div>
  }
}

export default Submissions
