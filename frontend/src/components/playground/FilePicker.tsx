import React from 'react';

interface FilePickerProps {
  onFileSelect: (files: File[]) => void;
  acceptedTypes?: string;
  multiple?: boolean;
}

const FilePicker: React.FC<FilePickerProps> = ({ 
  onFileSelect, 
  acceptedTypes = '*', 
  multiple = false 
}) => {
  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      onFileSelect(Array.from(files));
    }
  };

  return (
    <div className="relative">
      <input
        type="file"
        onChange={handleFileChange}
        accept={acceptedTypes}
        multiple={multiple}
        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
      />
      <div className="px-3 py-1.5 text-xs bg-gray-200 dark:bg-gray-700 rounded-lg cursor-pointer hover:bg-gray-300 dark:hover:bg-gray-600 transition">
        Choose File
      </div>
    </div>
  );
};

export default FilePicker;