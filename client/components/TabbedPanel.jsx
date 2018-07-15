import React from 'react'

class TabbedPanel extends React.Component {
  constructor (props) {
    super(props)
    this.state = {
      selected: 0
    }
  }

  render () {
    return (
      <React.Fragment>
        <div className='panel-tabs'>
          {
            this.props.panels.map((panel, i) => (
              <a
                key={i}
                className={i === this.state.selected ? 'is-active' : ''}
                onClick={() => this.setState({ selected: i })}
              >
                {panel.name}
              </a>
            ))
          }
        </div>
        <div className='panel-block'>
          {this.props.panels[this.state.selected].panel}
        </div>
      </React.Fragment>
    )
  }
}

export default TabbedPanel
