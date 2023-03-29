/// <reference types="cypress" />

// Welcome to Cypress!
//
// This spec file contains a variety of sample tests
// for a list app that are designed to demonstrate
// the power of writing tests in Cypress.
//
// To learn more about how Cypress works and
// what makes it such an awesome testing tool,
// please read our getting started guide:
// https://on.cypress.io/introduction-to-cypress

describe('trs login page', () => {
    beforeEach(() => {
        // Cypress starts out with a blank slate for each test
        // so we must tell it to visit our website with the `cy.visit()` command.
        // Since we want to visit the same URL at the start of all our tests,
        // we include it in our beforeEach function so that it runs before each test
        cy.visit('http://localhost:8002/accounts/login/')
    })

    it('show/hide password button', () => {
        cy.get('#password').should('have.attr', 'type', 'password')
        cy.get('#show_password').find('span.show-text').should('contain.text', 'Show')


        cy.get('#password').type('123456').should('have.value', '123456')
        cy.get('#show_password').click()
        cy.get('#password').should('have.attr', 'type', 'text')
        cy.get('#show_password').find('span.show-text').should('contain.text', 'Hide')

    })

    it('no email provided error displays', () => {
        cy.get('#password').type('123456!DSs')

        cy.get("button").contains("Sign in").click()
        cy.get('#email').should('have.class', 'govuk-input--error')
        cy.get('#email-error').should("contain.text", "Enter your email address")
    })

    it('incorrectly formatted email produces error', () => {
        cy.get('#email').type('testexample.com')
        cy.get("button").contains("Sign in").click()

        cy.get('#email').should('have.class', 'govuk-input--error')
        cy.get('#email-error').should("contain.text", "Enter your email address")
    })

    it('no password provided produces error', () => {
        cy.get('#email').type('test@example.com')
        cy.get("button").contains("Sign in").click()

        cy.get('#password').should('have.class', 'govuk-input--error')
        cy.get('#password-error').should("contain.text", "Enter your password")
    })

    it('incorrectly formatted password provided produces error', () => {
        cy.get('#email').type('test@example.com')
        cy.get('#password').type('123')
        cy.get("button").contains("Sign in").click()

        cy.get('#password').should('have.class', 'govuk-input--error')
        cy.get('#password-error').should("contain.text", "Enter a password that contains 8 or more characters")
    })

    it('login successful', () => {
        cy.get('#email').type('123@gmail.com')
        cy.get('#password').type('P4VjNndraE9L92c!')
        cy.get("button").contains("Sign in").click()

        cy.url().should('include', '/dashboard/')
    })

})
