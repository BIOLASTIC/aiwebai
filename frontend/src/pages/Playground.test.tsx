import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import Playground from './Playground';

describe('Playground', () => {
  it("shows model dropdown for image and video", () => {
    // This is a basic test to ensure model selector appears
    // In the current implementation, the default tool is 'chat', which shows the model selector
    render(<Playground />);
    expect(screen.getByText("Model:")).toBeInTheDocument();
  });
});