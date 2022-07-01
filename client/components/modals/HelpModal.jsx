import React from 'react'

import './../Modal.css'
import shortcutsMarkdown from './ShortcutsHelp.md'
import gradingPolicyMarkdown from './GradingPolicyHelp.md'

const HelpModal = (props) => (
  <div className={'modal ' + (props.page.title ? 'is-active' : '')}>
    <div className='modal-background' onClick={props.closeHelp} />
    <div className='modal-card'>
      <header className='modal-card-head'>
        <p className='modal-card-title'>
          {props.page.title}
        </p>
      </header>
      <section className='modal-card-body'>
        <div
          className='content'
          dangerouslySetInnerHTML={
            { __html: (props.page.content) }
}
        />
      </section>
      <footer className='modal-card-footer'>
        <div className='field is-grouped'>
          <button className='button is-fullwidth is-info is-footer' onClick={props.closeHelp}>
            Close
          </button>
        </div>
      </footer>
    </div>
    <button className='modal-close is-large' aria-label='close' onClick={props.closeHelp} />
  </div>
)

export const HELP_PAGES = {
  shortcuts: { title: 'Shortcuts', content: shortcutsMarkdown },
  gradingPolicy: { title: 'Auto-approve', content: gradingPolicyMarkdown }
}

export default HelpModal
