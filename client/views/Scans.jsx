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

class Scans extends React.Component {
  state = {
    scans: [],
    copies: [],
    examID: null,
    showOtherUploadOptions: false
  };

  updateScans = () => {
    api.get('scans/' + this.props.examID)
      .then(scans => {
        if (JSON.stringify(scans) !== JSON.stringify(this.state.scans)) {
          this.setState({
            scans: scans
          })
          this.updateMissingPages()
        }
      })
  }

  updateMissingPages = () => {
    api.get('copies/missing_pages/' + this.props.examID)
      .then(copies => {
        this.setState({
          copies: copies.map(copy => ({
            number: copy['number'],
            missing: copy['missing_pages']
          }))
        })
      })
  }

  onDropFile = (accepted, rejected, type) => {
    if (rejected.length > 0) {
      Notification.error('Please upload a PDF, ZIP or image.')
      return
    }
    accepted.map(file => {
      const data = new window.FormData()
      data.append('file', file)
      data.append('scan_type', type)
      api.post('scans/' + this.props.examID, data)
        .then(() => {
          this.updateScans()
        })
        .catch(resp => {
          Notification.error('Failed to upload file (see javascript console for details)')
          console.error('Failed to upload file:', resp)
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
            'to their copies',
            { 'duration': 5 }
          )
        }
      })
  }

  componentWillUnmount = () => {
    clearInterval(this.scanUpdater)
  }

  render () {
    const missingPages = this.state.copies.filter(c => c.missing.length > 0)

    const missingPagesStatus = (
      missingPages.length > 0
        ? <div>
          <p className='menu-label'>
            Missing Pages
          </p>
          <ul className='menu-list'>
            {missingPages.map(copy =>
              <li key={copy.number}>
                Copy {copy.number} is missing pages {copy.missing.join(', ')}
              </li>
            )}
          </ul>
        </div>
        : null
    )

    const acceptedTypes = 'application/pdf,application/zip,application/octet-stream,application/x-zip-compressed,multipart/x-zip,image/*'

    return <div>

      <Hero title='Scans' subtitle='Upload scans and check missing pages' />

      <section className='section'>

        <div className='container'>
          <div className='columns is-multiline is-centered'>
            <div className='column is-full has-text-centered'>
              <Dropzone accept={acceptedTypes} style={{}}
                activeStyle={{ borderStyle: 'dashed', width: 'fit-content', margin: 'auto' }}
                onDrop={(accepted, rejected) => this.onDropFile(accepted, rejected, 'normal')}
                disablePreview
                multiple>
                <DropzoneContent text='Choose a scan file…' center />
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
                    accept={acceptedTypes}
                    style={{}}
                    activeStyle={{ borderStyle: 'dashed', width: 'fit-content', margin: 'auto' }}
                    onDrop={(accepted, rejected) => this.onDropFile(accepted, rejected, 'raw')}
                    disablePreview
                    multiple>
                    <DropzoneContent text='Choose a scan file…' center />
                  </Dropzone>
                </div>
              </div>
            </div>
            <div className='column is-full has-text-centered'>
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
            </div>
          </div>
        </div>
      </section>
    </div>
  }
}

export default Scans
