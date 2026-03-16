import React from 'react';

interface FileData {
  id: string;
  name: string;
}

interface FilePickerProps {
  onFileSelect: (files: File[]) => void;
  selected?: FileData[];
  acceptedTypes?: string;
  multiple?: boolean;
}

const FilePicker: React.FC<FilePickerProps> = ({ 
  onFileSelect, 
  selected = [],
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
    <div className="space-y-2">
      {selected.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {selected.map(file => (
            <div 
              key={file.id} 
              className="px-2 py-1 text-xs bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 rounded-md"
            >
              {file.name}
            </div>
          ))}
        </div>
      )}
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
    </div>
  );
};

export default FilePicker;
