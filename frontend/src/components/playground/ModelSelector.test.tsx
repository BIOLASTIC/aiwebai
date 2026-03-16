import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ModelSelector from './ModelSelector';
import { modelApi } from '../../lib/api';

// Mock the modelApi
jest.mock('../../lib/api', () => ({
  modelApi: {
    getModelsByAccountAndFeature: jest.fn(),
  },
}));

describe('ModelSelector', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("loads models by account and feature", async () => {
    const mockModels = [
      {
        id: 1,
        provider_model_name: "gemini-pro",
        display_name: "Gemini Pro",
        family: "gemini"
      }
    ];
    
    (modelApi.getModelsByAccountAndFeature as jest.Mock).mockResolvedValue({ data: mockModels });

    render(<ModelSelector accountId="1" feature="video" />);
    
    expect(screen.getByText("Loading models...")).toBeInTheDocument();
    
    // Wait for the models to load
    expect(await screen.findByText("Gemini Pro")).toBeInTheDocument();
  });

  it("displays 'No video models' when no models are available", async () => {
    (modelApi.getModelsByAccountAndFeature as jest.Mock).mockResolvedValue({ data: [] });

    render(<ModelSelector accountId="1" feature="video" />);
    
    expect(await screen.findByText("No video models")).toBeInTheDocument();
  });

  it("renders null for unsupported features", () => {
    render(<ModelSelector accountId="1" feature="unsupported" />);
    
    expect(screen.queryByText("Model")).not.toBeInTheDocument();
  });

  it("renders for chat, image, and video features", async () => {
    const mockModels = [
      {
        id: 1,
        provider_model_name: "gemini-pro",
        display_name: "Gemini Pro",
        family: "gemini"
      }
    ];
    
    (modelApi.getModelsByAccountAndFeature as jest.Mock).mockResolvedValue({ data: mockModels });
    
    const { unmount } = render(<ModelSelector accountId="1" feature="chat" />);
    expect(await screen.findByText("Model")).toBeInTheDocument();
    
    unmount();
    render(<ModelSelector accountId="1" feature="image" />);
    expect(await screen.findByText("Model")).toBeInTheDocument();
    
    unmount();
    render(<ModelSelector accountId="1" feature="video" />);
    expect(await screen.findByText("Model")).toBeInTheDocument();
  });
});