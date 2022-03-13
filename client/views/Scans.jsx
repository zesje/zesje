import React from 'react'

import { toast } from 'bulma-toast'
import Dropzone from 'react-dropzone'
import PageVisibility from 'react-page-visibility'

import Hero from '../components/Hero.jsx'

import * as api from '../api.jsx'

const INTERVAL_FAST = 1000 // 1s
const INTERVAL_SLOW = 10000 // 10s

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
        : null}
    </div>
  )
}

class Scans extends React.Component {
  state = {
    scans: [],
    copies: [],
    examID: null,
    hasStudents: undefined
  };

  constructor (props) {
    super(props)
    this.scanUpdater = null
  }

  componentDidMount = () => {
    this.updateScans()
    // TODO: remove this when https://gitlab.kwant-project.org/zesje/zesje/issues/173
    //       has been solved. This is a
    api.get('students')
      .then(students => {
        this.setState({ hasStudents: students.length > 0 })
      })
  }

  componentWillUnmount = () => this.cancelScansUpdate()

  cancelScansUpdate = () => {
    if (this.scanUpdater) {
      clearInterval(this.scanUpdater)
      this.scanUpdater = null
      this.timeInterval = -1
    }
  }

  handleVisibilityChange = isVisible => {
    if (isVisible) {
      this.updateScans()
    } else {
      this.cancelScansUpdate()
    }
  }

  updateScans = () => {
    api.get('scans/' + this.props.examID)
      .then(scans => {
        if (JSON.stringify(scans) !== JSON.stringify(this.state.scans)) {
          this.setState({
            scans: scans
          })
          this.updateMissingPages()

          const hasRunningJobs = scans.some(scan => scan.status !== 'success')
          const newInterval = hasRunningJobs ? INTERVAL_FAST : INTERVAL_SLOW
          if (newInterval !== this.timeInterval) {
            console.log(hasRunningJobs)
            this.cancelScansUpdate()
            this.scanUpdater = setInterval(this.updateScans, newInterval)
            this.timeInterval = newInterval
          }
        }
      })
  }

  updateMissingPages = () =>
    api.get('copies/missing_pages/' + this.props.examID)
      .then(copies => this.setState({ copies }))

  onDropFile = (accepted, rejected) => {
    if (rejected.length > 0) {
      toast({ message: 'Please upload a PDF, ZIP or image.', type: 'is-danger' })
      return
    }

    accepted.forEach(file => {
      const data = new window.FormData()
      data.append('file', file)
      api.post('scans/' + this.props.examID, data)
        .then(this.updateScans)
        .catch(resp => {
          toast({ message: 'Failed to upload file (see javascript console for details)', type: 'is-danger' })
          console.error('Failed to upload file:', resp)
        })
    })
  }

  render () {
    const missingPages = this.state.copies.filter(c => c.missing_pages.length > 0)

    const missingPagesStatus = (
      missingPages.length > 0
        ? (
          <div>
            <p className='menu-label'>
              Missing Pages
            </p>
            <ul className='menu-list'>
              {missingPages.map(copy =>
                <li key={copy.number}>
                  Copy {copy.number} is missing pages {copy.missing_pages.join(', ')}
                </li>
              )}
            </ul>
          </div>
          )
        : null
    )

    const acceptedTypes = 'application/pdf,image/*,' +
      'application/zip,application/octet-stream,application/x-zip-compressed,multipart/x-zip'

    return (
      <div>

        <Hero title='Scans' subtitle='Upload scans and check missing pages' />

        <section className='section'>

          <div className='container'>
            {this.state.hasStudents === false &&
              <article className='message is-warning'>
                <div className='message-body'>
                  You have NOT yet uploaded any students. If you don&apos;t upload students before the scans
                  then we can&apos;t automatically assign students to their copies.
                </div>
              </article>
            }
            <div className='columns is-multiline is-centered'>
              <div className='column is-full has-text-centered'>
                <Dropzone
                  accept={acceptedTypes}
                  onDrop={(accepted, rejected) => this.onDropFile(accepted, rejected)}
                  multiple
                >
                  {({ getRootProps, getInputProps }) => (
                    <section className='container'>
                      <div {...getRootProps({ className: 'dropzone' })}>
                        <input {...getInputProps()} />
                        <p>Drag &apos;n&apos; drop or click to select scan files...</p>
                      </div>
                    </section>
                  )}
                </Dropzone>
              </div>
              <div className='column is-full has-text-centered'>
                <PageVisibility onChange={this.handleVisibilityChange}>
                  <aside className='menu'>
                    <p className='menu-label'>
                      Uploaded copies: {this.state.copies.length}
                    </p>

                    {missingPagesStatus}

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
                </PageVisibility>
              </div>
            </div>
          </div>
        </section>
      </div>
    )
  }
}

export default Scans
