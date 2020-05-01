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
  return (
    <div>
      {props.scan.name}&emsp;<i className={iconClass} />
      <i>&nbsp;{props.scan.message}</i>
    </div>
  )
}

class Scans extends React.Component {
  state = {
    scans: [],
    copies: [],
    examID: null
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

  onDropPDF = (accepted, rejected) => {
    if (rejected.length > 0) {
      Notification.error('Please upload a scan PDF.')
      return
    }
    accepted.map(file => {
      const data = new window.FormData()
      data.append('pdf', file)
      api.post('scans/' + this.props.examID, data)
        .then(() => {
          this.updateScans()
        })
        .catch(resp => {
          Notification.error('failed to upload pdf (see javascript console for details)')
          console.error('failed to upload PDF:', resp)
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

    return <div>

      <Hero title='Scans' subtitle='Upload scans and check missing pages' />

      <section className='section'>

        <div className='container'>
          <div className='columns'>
            <div className='column has-text-centered'>
              <Dropzone accept={'application/pdf'} style={{}}
                activeStyle={{ borderStyle: 'dashed', width: 'fit-content', margin: 'auto' }}
                onDrop={this.onDropPDF}
                disablePreview
                multiple
              >
                <DropzoneContent />
              </Dropzone>
              <br />
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