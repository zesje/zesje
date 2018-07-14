import React from 'react'
import Autosuggest from 'react-autosuggest'
import Fuse from 'fuse.js'

const theme = {
  input: {
    width: '25vw',
    minWidth: '225px'
  },
  suggestionsContainerOpen: {
    display: 'block',
    position: 'absolute',
    right: '0px',
    left: '0px',
    border: '1px solid #aaa',
    backgroundColor: '#fff',
    borderBottomLeftRadius: 4,
    borderBottomRightRadius: 4,
    zIndex: 2,
    maxHeight: '300px',
    overflowY: 'auto'
  },
  suggestion: {
    cursor: 'pointer',
    padding: '5px 10px'
  },
  suggestionHighlighted: {
    backgroundColor: '#ddd'
  }
}

class SearchBox extends React.Component {
  state = {
    value: '',
    suggestions: [],
    selectedID: null
  }

  static getDerivedStateFromProps (nextProps, prevState) {
    if (nextProps.selected.id !== prevState.selectedID) {
      return {
        value: nextProps.renderSelected(nextProps.selected),
        selectedID: nextProps.selected.id
      }
    }
    return null
  }

  onChange = (event, { newValue }) => {
    this.setState({
      value: newValue
    })
  }
  onBlur = () => {
    this.setState({
      value: this.props.renderSelected(this.props.selected)
    })
  }
  onFocus = () => {
    this.setState({
      value: ''
    })
  }
  onSuggestionSelected = (event, { suggestion }) => {
    this.props.setSelected(suggestion.id)
  }

  // Autosuggest will call this function every time you need to update suggestions.
  // You already implemented this logic above, so just use it.
  onSuggestionsFetchRequested = ({ value }) => {
    const options = {
      shouldSort: true,
      threshold: 0.6,
      location: 0,
      distance: 100,
      maxPatternLength: 32,
      minMatchCharLength: 1,
      keys: this.props.suggestionKeys
    }
    const fuse = new Fuse(this.props.options, options)
    const result = fuse.search(value)

    this.setState({
      suggestions: result
    })
  }

  // Autosuggest will call this function every time you need to clear suggestions.
  onSuggestionsClearRequested = () => {
    this.setState({
      suggestions: []
    })
  }

  render () {
    const { value, suggestions } = this.state

    // Autosuggest will pass through all these props to the input.
    const inputProps = {
      className: 'input is-rounded has-text-centered is-link',
      type: 'text',
      placeholder: this.props.placeholder,
      value,
      onChange: this.onChange,
      onFocus: this.onFocus,
      onBlur: this.onBlur
    }

    return (
      <Autosuggest
        suggestions={suggestions}
        onSuggestionsFetchRequested={this.onSuggestionsFetchRequested}
        onSuggestionsClearRequested={this.onSuggestionsClearRequested}
        onSuggestionSelected={this.onSuggestionSelected}
        getSuggestionValue={this.props.renderSelected}
        renderSuggestion={this.props.renderSuggestion}
        inputProps={inputProps}
        theme={theme}
        focusInputOnSuggestionClick={false}
        highlightFirstSuggestion
      />
    )
  }
}

export default SearchBox
