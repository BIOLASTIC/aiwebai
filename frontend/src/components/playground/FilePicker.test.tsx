import React from 'react';
import { render, screen } from '@testing-library/react';
import FilePicker from './FilePicker';

describe('FilePicker', () => {
  it("shows selected reference files", () => {
    render(<FilePicker selected={[{ id: "file_1", name: "ref.png" }]} onFileSelect={jest.fn()} />);
    expect(screen.getByText("ref.png")).toBeInTheDocument();
  });
});
