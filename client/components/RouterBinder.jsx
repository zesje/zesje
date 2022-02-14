import React from 'react'

import {
  useLocation,
  useNavigate,
  useParams
} from 'react-router-dom'

// Wrapper to access router hooks from react components
// https://github.com/remix-run/react-router/blob/5730e28a7472e3a1b967d95c5c4cc643c570d5c7/docs/faq.md

function withRouter (Component) {
  function ComponentWithRouterProp (props) {
    const location = useLocation()
    const navigate = useNavigate()
    const params = useParams()

    return (
      <Component
        {...props}
        router={{ location, navigate, params }}
      />
    )
  }

  return ComponentWithRouterProp
}

export default withRouter
